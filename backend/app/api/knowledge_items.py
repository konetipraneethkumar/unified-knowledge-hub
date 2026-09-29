from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import KnowledgeItemCreate, KnowledgeItemRead
from app.services.knowledge_items import (
	create_knowledge_item,
	get_knowledge_item,
	list_knowledge_items,
)


router = APIRouter(prefix="/knowledge-items", tags=["knowledge-items"])


@router.post(
	"",
	response_model=KnowledgeItemRead,
	status_code=status.HTTP_201_CREATED,
)
def create_knowledge_item_route(
	knowledge_item: KnowledgeItemCreate,
	db: Session = Depends(get_db),
) -> KnowledgeItemRead:
	return create_knowledge_item(db, knowledge_item)


@router.get("/{item_id}", response_model=KnowledgeItemRead)
def get_knowledge_item_route(
	item_id: int, db: Session = Depends(get_db)
) -> KnowledgeItemRead:
	item = get_knowledge_item(db, item_id)
	if item is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Knowledge item not found",
		)
	return item


@router.get("", response_model=list[KnowledgeItemRead])
def list_knowledge_items_route(
	db: Session = Depends(get_db),
	offset: int = Query(default=0, ge=0),
	limit: int = Query(default=100, ge=1, le=500),
) -> list[KnowledgeItemRead]:
	return list_knowledge_items(db, offset=offset, limit=limit)