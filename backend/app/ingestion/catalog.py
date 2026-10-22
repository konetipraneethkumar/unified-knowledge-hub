"""Persistence operations for normalized knowledge items.

These operations sit behind the ingestion boundary so HTTP routes do not own
database queries and connectors/sync jobs share one item representation.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeItem
from app.ingestion.local_context import (
	require_authorized_path,
	resolve_local_index_context,
)
from app.schemas import KnowledgeItemCreate


def create_knowledge_item(
	db: Session, knowledge_item: KnowledgeItemCreate, *, owner_id: int
) -> KnowledgeItem:
	context = resolve_local_index_context(
		db,
		owner_id=owner_id,
		connector_id=knowledge_item.connector_id,
		device_id=knowledge_item.device_id,
	)
	resource_path = require_authorized_path(knowledge_item.source_item_id, context)
	if knowledge_item.location is not None and require_authorized_path(
		knowledge_item.location, context
	) != resource_path:
		raise ValueError("location must identify the same local resource")
	item_data = knowledge_item.model_dump(
		exclude={"connector_id", "device_id", "location"}
	)
	item = KnowledgeItem(
		**item_data,
		owner_id=context.owner_id,
		connector_id=context.connector_id,
		device_id=context.device_id,
		source_item_id=str(resource_path),
		location=str(resource_path),
	)
	db.add(item)
	db.commit()
	db.refresh(item)
	return item


def get_knowledge_item(
	db: Session, item_id: int, *, owner_id: int
) -> KnowledgeItem | None:
	statement = select(KnowledgeItem).where(
		KnowledgeItem.id == item_id, KnowledgeItem.owner_id == owner_id
	)
	return db.scalar(statement)


def list_knowledge_items(
	db: Session, *, owner_id: int, offset: int = 0, limit: int = 100
) -> list[KnowledgeItem]:
	statement = (
		select(KnowledgeItem)
		.where(KnowledgeItem.owner_id == owner_id)
		.order_by(KnowledgeItem.id)
		.offset(offset)
		.limit(limit)
	)
	return list(db.scalars(statement).all())
