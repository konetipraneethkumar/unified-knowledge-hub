from collections.abc import Sequence
from math import isfinite, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeItem, KnowledgeItemEmbedding


def store_embedding(
	db: Session, item_id: int, embedding: Sequence[float]
) -> KnowledgeItemEmbedding:
	vector = _validated_vector(embedding)
	stored_embedding = db.get(KnowledgeItemEmbedding, item_id)
	if stored_embedding is None:
		stored_embedding = KnowledgeItemEmbedding(
			item_id=item_id, embedding=vector
		)
	else:
		stored_embedding.embedding = vector

	db.add(stored_embedding)
	db.commit()
	db.refresh(stored_embedding)
	return stored_embedding


def search_similar_knowledge_items(
	db: Session, query_embedding: Sequence[float], limit: int = 10, owner_id: int | None = None
) -> list[tuple[KnowledgeItem, float]]:
	if limit < 1:
		raise ValueError("limit must be a positive integer")
	query_vector = _validated_vector(query_embedding)

	if db.get_bind().dialect.name == "sqlite":
		statement = select(
			KnowledgeItem, KnowledgeItemEmbedding.embedding
		).join(
			KnowledgeItemEmbedding,
			KnowledgeItemEmbedding.item_id == KnowledgeItem.id,
		)
		if owner_id is not None:
			statement = statement.where(KnowledgeItem.owner_id == owner_id)
		scored_items = [
			(item, _cosine_similarity(query_vector, vector))
			for item, vector in db.execute(statement).all()
		]
		return sorted(
			scored_items, key=lambda result: (-result[1], result[0].id)
		)[:limit]

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


def _validated_vector(embedding: Sequence[float]) -> list[float]:
	vector = [float(value) for value in embedding]
	if not vector or not all(isfinite(value) for value in vector):
		raise ValueError("embedding must contain finite values")
	if not any(vector):
		raise ValueError("embedding must not be a zero vector")
	return vector


def _cosine_similarity(
	left: Sequence[float], right: Sequence[float]
) -> float:
	if len(left) != len(right):
		raise ValueError("embedding dimensions must match")
	left_norm = sqrt(sum(value * value for value in left))
	right_norm = sqrt(sum(value * value for value in right))
	return sum(a * b for a, b in zip(left, right)) / (
		left_norm * right_norm
	)
