from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeItem
from app.schemas import KnowledgeItemCreate


def create_knowledge_item(
	db: Session, knowledge_item: KnowledgeItemCreate
) -> KnowledgeItem:
	item = KnowledgeItem(**knowledge_item.model_dump())
	db.add(item)
	db.commit()
	db.refresh(item)
	return item


def get_knowledge_item(db: Session, item_id: int) -> KnowledgeItem | None:
	return db.get(KnowledgeItem, item_id)


def list_knowledge_items(
	db: Session, offset: int = 0, limit: int = 100
) -> list[KnowledgeItem]:
	statement = (
		select(KnowledgeItem)
		.order_by(KnowledgeItem.id)
		.offset(offset)
		.limit(limit)
	)
	return list(db.scalars(statement).all())