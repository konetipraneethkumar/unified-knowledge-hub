from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import KnowledgeItem


def search_knowledge_items(
	db: Session,
	query: str,
	offset: int = 0,
	limit: int = 20,
	owner_id: int | None = None,
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
	total = db.scalar(
		select(func.count())
		.select_from(KnowledgeItem)
		.where(search_filter)
	) or 0
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
	return list(db.scalars(statement).all()), total
