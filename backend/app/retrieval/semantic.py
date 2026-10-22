from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment.embeddings import validate_embedding
from app.models import KnowledgeItem, KnowledgeItemEmbedding


def search_similar_knowledge_items(
	db: Session,
	query_embedding: Sequence[float],
	limit: int = 10,
	owner_id: int | None = None,
) -> list[tuple[KnowledgeItem, float]]:
	if limit < 1:
		raise ValueError("limit must be a positive integer")
	query_vector = validate_embedding(query_embedding)

	distance = KnowledgeItemEmbedding.embedding.cosine_distance(
		query_vector
	).label("distance")
	statement = (
		select(KnowledgeItem, distance)
		.join(
			KnowledgeItemEmbedding,
			KnowledgeItemEmbedding.item_id == KnowledgeItem.id,
		)
		.order_by(distance, KnowledgeItem.id)
		.limit(limit)
	)
	if owner_id is not None:
		statement = statement.where(KnowledgeItem.owner_id == owner_id)
	return [
		(item, 1.0 - float(distance))
		for item, distance in db.execute(statement).all()
	]
