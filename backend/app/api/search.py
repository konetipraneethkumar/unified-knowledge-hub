import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.enrichment.embeddings import EmbeddingService, get_embedding_service
from app.llm.providers import (
	LLMConfigurationError,
	LLMProvider,
	LLMProviderError,
	get_llm_provider,
)
from app.llm.service import generate_grounded_answer
from app.models import User
from app.retrieval.context_builder import RagContextBuilder
from app.retrieval.hybrid import hybrid_search
from app.retrieval.lexical import search_knowledge_items
from app.schemas import (
	HybridKnowledgeItemSearchResponse,
	KnowledgeItemSearchResponse,
)
from app.schemas.rag import RagAnswerRequest, RagAnswerResponse


router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)
_NO_RESULTS_ANSWER = (
	"I couldn't find relevant information in your connected sources to answer that query."
)
_SAFE_SOURCE_METADATA_FIELDS = {
	"google_drive": {"drive_file_id", "parent_ids"},
	"gmail": {"sender", "subject", "message_id", "thread_id", "date_header"},
	"google_classroom": {
		"course_id",
		"course_name",
		"resource_id",
		"resource_type",
		"attachments",
	},
}


@router.get("/search", response_model=KnowledgeItemSearchResponse)
def search_knowledge_items_route(
	q: str = Query(min_length=1, max_length=200),
	offset: int = Query(default=0, ge=0),
	limit: int = Query(default=20, ge=1, le=100),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> KnowledgeItemSearchResponse:
	query = q.strip()
	if not query:
		raise HTTPException(status_code=422, detail="Query must not be blank")

	items, total = search_knowledge_items(
		db, query=query, offset=offset, limit=limit, owner_id=current_user.id
	)
	return KnowledgeItemSearchResponse(
		query=query,
		offset=offset,
		limit=limit,
		total=total,
		items=items,
	)


@router.get("/hybrid-search", response_model=HybridKnowledgeItemSearchResponse)
def hybrid_search_knowledge_items_route(
	q: str = Query(min_length=1, max_length=200),
	limit: int = Query(default=20, ge=1, le=100),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> HybridKnowledgeItemSearchResponse:
	query = q.strip()
	if not query:
		raise HTTPException(status_code=422, detail="Query must not be blank")

	results = hybrid_search(
		db, query=query, embedding_service=embedding_service, limit=limit, owner_id=current_user.id
	)
	return HybridKnowledgeItemSearchResponse(
		query=query,
		limit=limit,
		total=len(results),
		items=[
			{"item": result.item, "relevance_score": result.relevance_score}
			for result in results
		],
	)


@router.post("/api/v1/search/ask", response_model=RagAnswerResponse)
@router.post("/answer", response_model=RagAnswerResponse, include_in_schema=False)
def ask_search_route(
	request: RagAnswerRequest,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RagAnswerResponse:
	query = request.query.strip()
	if not query:
		raise HTTPException(status_code=422, detail="Query must not be blank")

	results = hybrid_search(
		db,
		query=query,
		embedding_service=embedding_service,
		limit=settings.RAG_TOP_K,
		owner_id=current_user.id,
	)
	context = RagContextBuilder().build(query, results)
	if not context.sources:
		return RagAnswerResponse(
			query=query,
			answer=_NO_RESULTS_ANSWER,
			status="no_results",
			sources=[],
		)

	try:
		provider: LLMProvider = get_llm_provider()
		generated = generate_grounded_answer(query, context, provider)
	except LLMConfigurationError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
	except LLMProviderError as error:
		raise HTTPException(status_code=error.status_code, detail=str(error)) from error
	except Exception as error:
		logger.exception("Unexpected language model failure")
		raise HTTPException(
			status_code=502,
			detail="The language model could not generate an answer.",
		) from error

	return RagAnswerResponse(
		query=query,
		answer=generated.answer,
		status="answered",
		sources=[
			{
				"source_id": source.source_id,
				"source_type": source.source_type,
				"title": source.title,
				"date": source.date,
				"evidence": source.evidence,
				"trusted_source_reference": {
					"location": source.trusted_source_reference.location,
					"web_url": source.trusted_source_reference.web_url,
					"file_path": source.trusted_source_reference.file_path,
					"parent_location": source.trusted_source_reference.parent_location,
					"metadata": _safe_source_metadata(
						source.source_type,
						source.trusted_source_reference.metadata,
					),
				},
			}
			for source in generated.sources
		],
	)


def _safe_source_metadata(
	source_type: str, metadata: dict | None
) -> dict | None:
	"""Expose only connector locator fields, never arbitrary credential fields."""
	if metadata is None:
		return None
	allowed_fields = _SAFE_SOURCE_METADATA_FIELDS.get(source_type)
	if allowed_fields is None:
		return None
	safe_metadata = {
		key: value for key, value in metadata.items() if key in allowed_fields
	}
	if source_type == "google_classroom":
		attachments = safe_metadata.get("attachments")
		if isinstance(attachments, list):
			safe_metadata["attachments"] = [
				{
					key: value
					for key, value in attachment.items()
					if key in {"type", "title", "id", "url"}
				}
				for attachment in attachments
				if isinstance(attachment, dict)
			]
	return safe_metadata
