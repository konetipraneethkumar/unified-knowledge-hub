from datetime import datetime, timedelta, timezone
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, hash_secret
from app.models import Device, Pairing, User
from app.schemas.connectors import DeviceCredentialRead, DeviceRead, PairingCompleteRequest, PairingRead, PairingRequest

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Device]:
    return list(db.scalars(select(Device).where(Device.owner_id == current_user.id).order_by(Device.created_at)).all())


@router.post("/pair", response_model=PairingRead, status_code=status.HTTP_201_CREATED)
def create_pairing(request: PairingRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PairingRead:
    code = secrets.token_urlsafe(12)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PAIRING_CODE_TTL_MINUTES)
    db.add(Pairing(owner_id=current_user.id, code_hash=hash_secret(code), expires_at=expires_at))
    db.commit()
    return PairingRead(code=code, expires_at=expires_at)


@router.post("/pair/complete", response_model=DeviceCredentialRead, status_code=status.HTTP_201_CREATED)
def complete_pairing(request: PairingCompleteRequest, db: Session = Depends(get_db)) -> DeviceCredentialRead:
    pairing = db.scalar(select(Pairing).where(Pairing.code_hash == hash_secret(request.code)))
    now = datetime.now(timezone.utc)
    if pairing is None or pairing.used_at is not None or pairing.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pairing code is invalid, expired, or already used")
    credential = secrets.token_urlsafe(32)
    device = Device(id=str(uuid.uuid4()), owner_id=pairing.owner_id, name=request.name.strip(), credential_hash=hash_secret(credential), last_seen_at=now)
    pairing.used_at = now
    db.add(device)
    db.commit()
    db.refresh(device)
    return DeviceCredentialRead(device=device, credential=credential)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_device(device_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    device = db.scalar(select(Device).where(Device.id == device_id, Device.owner_id == current_user.id))
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    device.revoked_at = datetime.now(timezone.utc)
    db.commit()
