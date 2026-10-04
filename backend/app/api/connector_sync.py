from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import Connector, User
from app.schemas.connectors import ConnectorSyncResult
from app.sync.connectors import run_connector_sync, sync_connector_in_background

router = APIRouter(prefix="/api/v1/connectors", tags=["connector-sync"])


@router.post("/{connector_id}/sync", response_model=ConnectorSyncResult)
def sync_connector(
	connector_id: str,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
) -> ConnectorSyncResult:
	connector = db.scalar(
		select(Connector).where(
			Connector.id == connector_id,
			Connector.owner_id == current_user.id,
		)
	)
	if connector is None:
		raise HTTPException(status_code=404, detail="Connector not found.")
	return run_connector_sync(db, connector)


def queue_initial_sync(background_tasks: BackgroundTasks, connector: Connector) -> None:
	background_tasks.add_task(sync_connector_in_background, connector.id)
