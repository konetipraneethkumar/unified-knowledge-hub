"""Opaque bearer-session and device-credential helpers."""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import AuthToken, Device, User

password_hasher = PasswordHasher()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def issue_user_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthToken(user_id=user.id, token_hash=hash_secret(token), expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_TOKEN_TTL_HOURS)))
    db.commit()
    return token


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = db.scalar(select(AuthToken).where(AuthToken.token_hash == hash_secret(credentials.credentials)))
    now = datetime.now(timezone.utc)
    if token is None or token.revoked_at is not None or token.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


def get_active_device(device_id: str, credential: str, db: Session) -> Device:
    device = db.get(Device, device_id)
    if device is None or device.credential_hash != hash_secret(credential) or device.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked device credential")
    return device
