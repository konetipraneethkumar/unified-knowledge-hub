from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import KnowledgeItem
from app.services.embeddings import EmbeddingService
from app.services.knowledge_items import search_knowledge_items
from app.services.vector_storage import search_similar_knowledge_items


@dataclass(frozen=True)
class RankedKnowledgeItem:
	item: KnowledgeItem
	relevance_score: float


def fuse_ranked_results(
	keyword_results: list[KnowledgeItem],
	vector_results: list[tuple[KnowledgeItem, float]],
	*,
	limit: int = 20,
	rank_constant: int = 60,
) -> list[RankedKnowledgeItem]:
	if limit < 1:
		raise ValueError("limit must be a positive integer")
	if rank_constant < 0:
		raise ValueError("rank_constant must not be negative")

	items_by_id: dict[int, KnowledgeItem] = {}
	scores: dict[int, float] = {}
	for rank, item in enumerate(keyword_results, start=1):
		items_by_id[item.id] = item
		scores[item.id] = scores.get(item.id, 0.0) + 1 / (
			rank_constant + rank
		)
	for rank, (item, _similarity) in enumerate(vector_results, start=1):
		items_by_id[item.id] = item
		scores[item.id] = scores.get(item.id, 0.0) + 1 / (
			rank_constant + rank
		)

	ranked_items = [
		RankedKnowledgeItem(item=items_by_id[item_id], relevance_score=score)
		for item_id, score in scores.items()
	]
	return sorted(
		ranked_items,
		key=lambda result: (-result.relevance_score, result.item.id),
	)[:limit]


def hybrid_search(
	db: Session,
	query: str,
	embedding_service: EmbeddingService,
	*,
	limit: int = 20,
	rank_constant: int = 60,
	owner_id: int | None = None,
) -> list[RankedKnowledgeItem]:
	if limit < 1:
		raise ValueError("limit must be a positive integer")
	candidate_limit = limit * 3
	keyword_results, _total = search_knowledge_items(
		db, query=query, limit=candidate_limit, owner_id=owner_id
	)
	query_embeddings = embedding_service.embed([query])
	if len(query_embeddings) != 1:
		raise ValueError("embedding service must return one vector per input")
	vector_results = search_similar_knowledge_items(
		db, query_embeddings[0], limit=candidate_limit, owner_id=owner_id
	)
	return fuse_ranked_results(
		keyword_results,
		vector_results,
		limit=limit,
		rank_constant=rank_constant,
	)
