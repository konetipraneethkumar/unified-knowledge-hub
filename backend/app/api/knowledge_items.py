from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import KnowledgeItem
from app.schemas import KnowledgeItemCreate, KnowledgeItemListResponse, KnowledgeItemRead
from app.ingestion.catalog import (
	create_knowledge_item,
	get_knowledge_item,
	list_knowledge_items,
)


router = APIRouter(prefix="/knowledge-items", tags=["knowledge-items"])


@router.get("/page", response_model=KnowledgeItemListResponse)
def list_knowledge_items_page(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	offset: int = Query(default=0, ge=0),
	limit: int = Query(default=20, ge=1, le=100),
	q: str = Query(default="", max_length=200),
	source: str | None = Query(default=None, min_length=1, max_length=100),
	item_type: str | None = Query(default=None, min_length=1, max_length=100),
	date_from: date | None = Query(default=None),
	date_to: date | None = Query(default=None),
) -> KnowledgeItemListResponse:
	filters = [KnowledgeItem.owner_id == current_user.id]
	query = q.strip()
	if query:
		pattern = f"%{query}%"
		filters.append(
			or_(
				KnowledgeItem.title.ilike(pattern),
				KnowledgeItem.location.ilike(pattern),
				KnowledgeItem.summary.ilike(pattern),
				KnowledgeItem.source.ilike(pattern),
			)
		)
	if source:
		filters.append(KnowledgeItem.source == source)
	if item_type:
		filters.append(KnowledgeItem.item_type == item_type)
	item_date = func.coalesce(
		KnowledgeItem.modified_at, KnowledgeItem.file_created_at
	)
	if date_from:
		filters.append(
			item_date
			>= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
		)
	if date_to:
		filters.append(
			item_date
			< datetime.combine(date_to, time.max, tzinfo=timezone.utc)
		)
	criteria = tuple(filters)
	total = db.scalar(
		select(func.count(KnowledgeItem.id)).where(*criteria)
	) or 0
	items = list(
		db.scalars(
			select(KnowledgeItem)
			.where(*criteria)
			.order_by(KnowledgeItem.indexed_at.desc(), KnowledgeItem.id.desc())
			.offset(offset)
			.limit(limit)
		).all()
	)
	return KnowledgeItemListResponse(
		offset=offset,
		limit=limit,
		total=total,
		items=items,
	)


@router.get("/sources", response_model=list[str])
def list_knowledge_sources(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> list[str]:
	return list(
		db.scalars(
			select(KnowledgeItem.source)
			.where(KnowledgeItem.owner_id == current_user.id)
			.distinct()
			.order_by(KnowledgeItem.source)
		).all()
	)


@router.get("/item-types", response_model=list[str])
def list_knowledge_item_types(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> list[str]:
	return list(
		db.scalars(
			select(KnowledgeItem.item_type)
			.where(
				KnowledgeItem.owner_id == current_user.id,
				KnowledgeItem.item_type.is_not(None),
			)
			.distinct()
			.order_by(KnowledgeItem.item_type)
		).all()
	)


@router.get("/count")
def count_knowledge_items(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> dict[str, int]:
	total = db.scalar(
		select(func.count(KnowledgeItem.id)).where(
			KnowledgeItem.owner_id == current_user.id
		)
	)
	return {"total": total or 0}


@router.get("/recent", response_model=list[KnowledgeItemRead])
def recent_knowledge_items(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	limit: int = Query(default=5, ge=1, le=20),
) -> list[KnowledgeItem]:
	return list(
		db.scalars(
			select(KnowledgeItem)
			.where(KnowledgeItem.owner_id == current_user.id)
			.order_by(KnowledgeItem.indexed_at.desc(), KnowledgeItem.id.desc())
			.limit(limit)
		).all()
	)


@router.post(
	"",
	response_model=KnowledgeItemRead,
	status_code=status.HTTP_201_CREATED,
)
def create_knowledge_item_route(
	knowledge_item: KnowledgeItemCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> KnowledgeItemRead:
	return create_knowledge_item(db, knowledge_item, owner_id=current_user.id)


@router.get("/{item_id}", response_model=KnowledgeItemRead)
def get_knowledge_item_route(
	item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> KnowledgeItemRead:
	item = get_knowledge_item(db, item_id, current_user.id)
	if item is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Knowledge item not found",
		)
	return item


@router.get("", response_model=list[KnowledgeItemRead])
def list_knowledge_items_route(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	offset: int = Query(default=0, ge=0),
	limit: int = Query(default=100, ge=1, le=500),
) -> list[KnowledgeItemRead]:
	return list_knowledge_items(db, offset=offset, limit=limit, owner_id=current_user.id)
