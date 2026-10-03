from sqlalchemy import case, func, or_, select
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


def get_knowledge_item(db: Session, item_id: int, owner_id: int | None = None) -> KnowledgeItem | None:
	statement = select(KnowledgeItem).where(KnowledgeItem.id == item_id)
	if owner_id is not None:
		statement = statement.where(KnowledgeItem.owner_id == owner_id)
	return db.scalar(statement)


def list_knowledge_items(
	db: Session, offset: int = 0, limit: int = 100, owner_id: int | None = None
) -> list[KnowledgeItem]:
	statement = (
		select(KnowledgeItem)
		.order_by(KnowledgeItem.id)
		.offset(offset)
		.limit(limit)
	)
	if owner_id is not None:
		statement = statement.where(KnowledgeItem.owner_id == owner_id)
	return list(db.scalars(statement).all())


def search_knowledge_items(
	db: Session, query: str, offset: int = 0, limit: int = 20, owner_id: int | None = None
) -> tuple[list[KnowledgeItem], int]:
	escaped_query = (
		query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
	)
	pattern = f"%{escaped_query}%"
	prefix_pattern = f"{escaped_query}%"
	search_filter = or_(
		KnowledgeItem.title.ilike(pattern, escape="\\"),
		KnowledgeItem.summary.ilike(pattern, escape="\\"),
		KnowledgeItem.content.ilike(pattern, escape="\\"),
		KnowledgeItem.source.ilike(pattern, escape="\\"),
		KnowledgeItem.item_type.ilike(pattern, escape="\\"),
	)
	if owner_id is not None:
		search_filter = search_filter & (KnowledgeItem.owner_id == owner_id)
	count_statement = (
		select(func.count())
		.select_from(KnowledgeItem)
		.where(search_filter)
	)
	total = db.scalar(count_statement) or 0
	statement = (
		select(KnowledgeItem)
		.where(search_filter)
		.order_by(
			case(
				(KnowledgeItem.title.ilike(escaped_query, escape="\\"), 0),
				(KnowledgeItem.title.ilike(prefix_pattern, escape="\\"), 1),
				(KnowledgeItem.title.ilike(pattern, escape="\\"), 2),
				(KnowledgeItem.summary.ilike(escaped_query, escape="\\"), 3),
				(KnowledgeItem.summary.ilike(prefix_pattern, escape="\\"), 4),
				(KnowledgeItem.summary.ilike(pattern, escape="\\"), 5),
				(KnowledgeItem.content.ilike(escaped_query, escape="\\"), 6),
				(KnowledgeItem.content.ilike(prefix_pattern, escape="\\"), 7),
				(KnowledgeItem.content.ilike(pattern, escape="\\"), 8),
				(
					or_(
						KnowledgeItem.source.ilike(escaped_query, escape="\\"),
						KnowledgeItem.item_type.ilike(escaped_query, escape="\\"),
					),
					9,
				),
				(
					or_(
						KnowledgeItem.source.ilike(prefix_pattern, escape="\\"),
						KnowledgeItem.item_type.ilike(prefix_pattern, escape="\\"),
					),
					10,
				),
				else_=11,
			),
			KnowledgeItem.id,
		)
		.offset(offset)
		.limit(limit)
	)
	items = list(db.scalars(statement).all())
	return items, total
