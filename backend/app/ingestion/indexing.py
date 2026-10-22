from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.enrichment.embeddings import validate_embedding
from app.models import KnowledgeItemEmbedding


def store_embedding(
	db: Session, item_id: int, embedding: Sequence[float]
) -> KnowledgeItemEmbedding:
	vector = validate_embedding(embedding)
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
