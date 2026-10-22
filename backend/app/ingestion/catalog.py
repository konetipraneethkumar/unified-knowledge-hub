"""Persistence operations for normalized knowledge items.

These operations sit behind the ingestion boundary so HTTP routes do not own
database queries and connectors/sync jobs share one item representation.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeItem
from app.schemas import KnowledgeItemCreate


def create_knowledge_item(
	db: Session, knowledge_item: KnowledgeItemCreate, owner_id: int | None = None
) -> KnowledgeItem:
	item = KnowledgeItem(**knowledge_item.model_dump(), owner_id=owner_id)
	db.add(item)
	db.commit()
	db.refresh(item)
	return item


def get_knowledge_item(
	db: Session, item_id: int, owner_id: int | None = None
) -> KnowledgeItem | None:
	statement = select(KnowledgeItem).where(KnowledgeItem.id == item_id)
	if owner_id is not None:
		statement = statement.where(KnowledgeItem.owner_id == owner_id)
	return db.scalar(statement)


def list_knowledge_items(
	db: Session, offset: int = 0, limit: int = 100, owner_id: int | None = None
) -> list[KnowledgeItem]:
	statement = select(KnowledgeItem).order_by(KnowledgeItem.id).offset(offset).limit(limit)
	if owner_id is not None:
		statement = statement.where(KnowledgeItem.owner_id == owner_id)
	return list(db.scalars(statement).all())
