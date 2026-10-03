from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Connector, Device, User
from app.schemas.connectors import ConnectorCreate, ConnectorRead

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _owned_connector(db: Session, connector_id: str, user_id: int) -> Connector:
    connector = db.scalar(select(Connector).where(Connector.id == connector_id, Connector.owner_id == user_id))
    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    return connector


@router.get("", response_model=list[ConnectorRead])
def list_connectors(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Connector]:
    return list(db.scalars(select(Connector).where(Connector.owner_id == current_user.id).order_by(Connector.created_at)).all())


@router.post("", response_model=ConnectorRead, status_code=status.HTTP_201_CREATED)
def create_connector(request: ConnectorCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Connector:
    if request.connector_type != "LOCAL":
        raise HTTPException(status_code=422, detail="Only LOCAL connectors are implemented")
    if request.device_id is None or request.authorized_root is None:
        raise HTTPException(status_code=422, detail="A local connector requires device_id and authorized_root")
    device = db.scalar(select(Device).where(Device.id == request.device_id, Device.owner_id == current_user.id, Device.revoked_at.is_(None)))
    if device is None:
        raise HTTPException(status_code=404, detail="Active device not found")
    root = Path(request.authorized_root).expanduser().resolve()
    connector = Connector(id=str(uuid.uuid4()), owner_id=current_user.id, device_id=device.id, connector_type="LOCAL", provider="local_filesystem", name=request.name.strip(), authorized_root=str(root))
    db.add(connector)
    db.commit()
    db.refresh(connector)
    return connector


@router.get("/{connector_id}", response_model=ConnectorRead)
def get_connector(connector_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Connector:
    return _owned_connector(db, connector_id, current_user.id)


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_connector(connector_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    connector = _owned_connector(db, connector_id, current_user.id)
    connector.status = "revoked"
    connector.revoked_at = datetime.now(timezone.utc)
    db.commit()
