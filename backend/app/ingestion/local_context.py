"""Authorization and path-boundary checks for local indexing."""
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Connector, Device


class LocalIndexContextError(ValueError):
	"""Raised when a local indexing request is not authorized."""


@dataclass(frozen=True)
class LocalIndexContext:
	owner_id: int
	connector_id: str
	device_id: str
	authorized_root: Path


def resolve_local_index_context(
	db: Session, *, owner_id: int, connector_id: str, device_id: str
) -> LocalIndexContext:
	connector = db.scalar(
		select(Connector).where(
			Connector.id == connector_id,
			Connector.owner_id == owner_id,
			Connector.device_id == device_id,
			Connector.connector_type == "LOCAL",
			Connector.provider == "local_filesystem",
			Connector.status == "active",
			Connector.revoked_at.is_(None),
		)
	)
	device = db.scalar(
		select(Device).where(
			Device.id == device_id,
			Device.owner_id == owner_id,
			Device.revoked_at.is_(None),
		)
	)
	if connector is None or device is None or not connector.authorized_root:
		raise LocalIndexContextError("local indexing context is not authorized")
	return LocalIndexContext(
		owner_id=owner_id,
		connector_id=connector.id,
		device_id=device.id,
		authorized_root=Path(connector.authorized_root).resolve(),
	)


def require_authorized_path(path: str | Path, context: LocalIndexContext) -> Path:
	resolved_path = Path(path).resolve()
	try:
		resolved_path.relative_to(context.authorized_root)
	except ValueError as error:
		raise LocalIndexContextError("path is outside the connector authorized root") from error
	return resolved_path
