"""Password, JWT, refresh-token, and OAuth-state security primitives."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import OAuthState, RefreshToken, User

password_hasher = PasswordHasher()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user.id), "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.SECRET_KEY.get_secret_value().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> int:
    try:
        header, payload, signature = token.split(".")
        expected = _b64(hmac.new(settings.SECRET_KEY.get_secret_value().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        claims = json.loads(_unb64(payload))
        if not isinstance(claims.get("sub"), str) or int(claims["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return int(claims["sub"])
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")


def issue_refresh_token(db: Session, user: User) -> str:
    raw = secrets.token_urlsafe(48)
    db.add(RefreshToken(user_id=user.id, token_hash=hash_secret(raw), expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)))
    db.commit()
    return raw


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str]:
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_secret(raw_token)))
    now = datetime.now(timezone.utc)
    if token is None or token.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if token.revoked_at is not None:
        for active in db.scalars(select(RefreshToken).where(RefreshToken.user_id == token.user_id, RefreshToken.revoked_at.is_(None))).all():
            active.revoked_at = now
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reuse detected")
    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive account")
    replacement = secrets.token_urlsafe(48)
    child = RefreshToken(user_id=user.id, token_hash=hash_secret(replacement), expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    db.add(child)
    db.flush()
    token.revoked_at = now
    token.replaced_by_token_id = child.id
    db.commit()
    return user, replacement


def create_oauth_state(db: Session, *, user_id: int | None, purpose: str, nonce: str | None = None) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(OAuthState(state_hash=hash_secret(raw), user_id=user_id, purpose=purpose, nonce=nonce, expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    db.commit()
    return raw


def consume_oauth_state(db: Session, raw: str, *, purpose: str, user_id: int | None = None) -> OAuthState:
    record = db.scalar(select(OAuthState).where(OAuthState.state_hash == hash_secret(raw), OAuthState.purpose == purpose))
    now = datetime.now(timezone.utc)
    if record is None or record.used_at is not None or record.expires_at.replace(tzinfo=timezone.utc) <= now or (user_id is not None and record.user_id != user_id):
        raise HTTPException(status_code=400, detail="Invalid, expired, or mismatched OAuth state")
    record.used_at = now
    db.commit()
    return record


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    user = db.get(User, decode_access_token(credentials.credentials))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account")
    return user
