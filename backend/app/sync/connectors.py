"""Run connector syncs and persist their normalized source snapshots."""
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.sources import IngestionResult, index_source_documents
from app.models import Connector, ConnectorCredential, Device, KnowledgeItem
from app.schemas.connectors import ConnectorSyncResult
from app.sync.google import (
	GoogleSourceError,
	fetch_google_documents,
	get_connector_access_token,
)
from app.sync.local_filesystem import index_local_directory

logger = logging.getLogger(__name__)


def run_connector_sync(db: Session, connector: Connector) -> ConnectorSyncResult:
	if connector.revoked_at is not None or connector.status == "revoked":
		raise HTTPException(status_code=409, detail="This connector has been revoked.")

	connector.status = "syncing"
	db.commit()
	try:
		if connector.connector_type == "LOCAL":
			result = _sync_local_connector(db, connector)
		elif connector.connector_type in {
			"GOOGLE_DRIVE",
			"GMAIL",
			"GOOGLE_CLASSROOM",
		}:
			result = _sync_google_connector(db, connector)
		else:
			raise HTTPException(
				status_code=422,
				detail=f"Connector type {connector.connector_type!r} cannot be synced.",
			)
	except Exception:
		db.rollback()
		current_connector = db.get(Connector, connector.id)
		if current_connector is not None:
			current_connector.status = "error"
			db.commit()
		raise

	connector = db.get(Connector, connector.id)
	if connector is None:
		raise HTTPException(status_code=404, detail="Connector was removed during sync.")
	connector.status = "active"
	connector.last_sync_at = datetime.now(timezone.utc)
	db.commit()
	return ConnectorSyncResult(
		connector_id=connector.id,
		status="completed_with_errors" if result.failed else "completed",
		processed=result.processed,
		skipped=result.skipped,
		failed=result.failed,
		deleted=result.deleted,
		errors=list(result.errors),
	)


def _sync_local_connector(db: Session, connector: Connector) -> IngestionResult:
	device = db.scalar(
		select(Device).where(
			Device.id == connector.device_id,
			Device.owner_id == connector.owner_id,
			Device.revoked_at.is_(None),
		)
	)
	if device is None:
		raise HTTPException(
			status_code=403,
			detail="Pair an active device before syncing this local folder.",
		)
	if not settings.LOCAL_STORAGE_ROOT:
		raise HTTPException(status_code=503, detail="Local storage is not configured.")
	if not connector.authorized_root:
		raise HTTPException(status_code=422, detail="The local connector has no authorized root.")

	configured_root = Path(settings.LOCAL_STORAGE_ROOT).resolve()
	requested_root = Path(connector.authorized_root).resolve()
	try:
		requested_root.relative_to(configured_root)
	except ValueError as error:
		raise HTTPException(
			status_code=403,
			detail="The local connector path is outside the configured storage root.",
		) from error
	if not requested_root.is_dir():
		raise HTTPException(status_code=404, detail="The authorized local folder is unavailable.")

	before_ids = set(
		db.scalars(
			select(KnowledgeItem.source_item_id).where(
				KnowledgeItem.connector_id == connector.id
			)
		).all()
	)
	items = index_local_directory(
		db,
		requested_root,
		owner_id=connector.owner_id,
		connector_id=connector.id,
		device_id=connector.device_id,
	)
	after_ids = set(
		db.scalars(
			select(KnowledgeItem.source_item_id).where(
				KnowledgeItem.connector_id == connector.id
			)
		).all()
	)
	processed = sum(item.processing_status == "processed" for item in items)
	failed_items = [item for item in items if item.processing_status == "failed"]
	returned_ids = {item.source_item_id for item in items}
	return IngestionResult(
		processed=processed,
		skipped=len(after_ids - returned_ids),
		failed=len(failed_items),
		deleted=len(before_ids - after_ids),
		errors=tuple(
			f"{item.title}: {item.processing_error or 'file processing failed'}"[:500]
			for item in failed_items
		),
	)


def _sync_google_connector(db: Session, connector: Connector) -> IngestionResult:
	credential = db.scalar(
		select(ConnectorCredential).where(
			ConnectorCredential.connector_id == connector.id
		)
	)
	if credential is None:
		raise HTTPException(
			status_code=409,
			detail="Google credentials are missing. Reconnect this account.",
		)

	try:
		access_token = get_connector_access_token(db, credential)
		documents = fetch_google_documents(connector, access_token)
		return index_source_documents(db, connector, documents)
	except GoogleSourceError as error:
		raise HTTPException(status_code=error.status_code, detail=str(error)) from error


def sync_connector_in_background(connector_id: str) -> None:
	from app.core.database import SessionLocal

	db = SessionLocal()
	try:
		connector = db.get(Connector, connector_id)
		if connector is None or connector.revoked_at is not None:
			return
		result = run_connector_sync(db, connector)
		if result.failed:
			logger.warning(
				"Connector %s indexed with %s failed items",
				connector_id,
				result.failed,
			)
	except Exception:
		logger.exception("Initial sync failed for connector %s", connector_id)
	finally:
		db.close()
