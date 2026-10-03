from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.retrieval.hybrid import hybrid_search
from app.schemas import (
	HybridKnowledgeItemSearchResponse,
	KnowledgeItemSearchResponse,
)
from app.services.embeddings import EmbeddingService, get_embedding_service
from app.services.knowledge_items import search_knowledge_items


router = APIRouter(tags=["search"])


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
