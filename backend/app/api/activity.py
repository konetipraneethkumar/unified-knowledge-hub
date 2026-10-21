from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import ConnectorSyncActivity, SearchHistory, User
from app.schemas.activity import (
    ConnectorSyncActivityRead,
    SearchHistoryCreate,
    SearchHistoryRead,
)

router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


@router.get("/search-history", response_model=list[SearchHistoryRead])
def list_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[SearchHistory]:
    return list(
        db.scalars(
            select(SearchHistory)
            .where(SearchHistory.owner_id == current_user.id)
            .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/search-history",
    response_model=SearchHistoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_search_history(
    request: SearchHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchHistory:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query must not be blank")
    entry = SearchHistory(
        owner_id=current_user.id,
        query=query,
        mode=request.mode,
        result_count=request.result_count,
        source_count=request.source_count,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/search-history", status_code=status.HTTP_204_NO_CONTENT)
def delete_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    entries = db.scalars(
        select(SearchHistory).where(SearchHistory.owner_id == current_user.id)
    ).all()
    for entry in entries:
        db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sync", response_model=list[ConnectorSyncActivityRead])
def list_sync_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ConnectorSyncActivity]:
    return list(
        db.scalars(
            select(ConnectorSyncActivity)
            .where(ConnectorSyncActivity.owner_id == current_user.id)
            .order_by(
                ConnectorSyncActivity.created_at.desc(),
                ConnectorSyncActivity.id.desc(),
            )
            .limit(limit)
        ).all()
    )
