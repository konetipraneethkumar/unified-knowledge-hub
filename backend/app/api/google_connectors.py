from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid

from app.connectors.google import authorization_url, encrypt_token, exchange_google_code, expiry_from_response
from app.core.config import settings
from app.core.database import get_db
from app.core.security import consume_oauth_state, create_oauth_state, get_current_active_user
from app.models import Connector, ConnectorCredential, User
from app.api.connector_sync import queue_initial_sync

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])
_CONFIG = {
    "google-drive": ("GOOGLE_DRIVE", settings.GOOGLE_DRIVE_REDIRECT_URI, "https://www.googleapis.com/auth/drive.readonly"),
    "gmail": ("GMAIL", settings.GMAIL_REDIRECT_URI, "https://www.googleapis.com/auth/gmail.readonly"),
    "google-classroom": ("GOOGLE_CLASSROOM", settings.GOOGLE_CLASSROOM_REDIRECT_URI, "https://www.googleapis.com/auth/classroom.courses.readonly https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly https://www.googleapis.com/auth/classroom.coursework.me.readonly https://www.googleapis.com/auth/classroom.announcements.readonly"),
}


def _config(kind: str) -> tuple[str, str, str]:
    if kind not in _CONFIG: raise HTTPException(status_code=404, detail="Connector not found")
    return _CONFIG[kind]


@router.get("/{kind}/connect")
def connect(kind: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> RedirectResponse:
    _, redirect_uri, scope = _config(kind)
    state = create_oauth_state(db, user_id=current_user.id, purpose=f"connector:{kind}")
    return RedirectResponse(authorization_url(redirect_uri=redirect_uri, scope=scope, state=state))


@router.get("/{kind}/connect-url")
def connect_url(
    kind: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _, redirect_uri, scope = _config(kind)
    state = create_oauth_state(db, user_id=current_user.id, purpose=f"connector:{kind}")
    return {"url": authorization_url(redirect_uri=redirect_uri, scope=scope, state=state)}


@router.get("/{kind}/callback")
def callback(
    kind: str,
    background_tasks: BackgroundTasks,
    code: str = Query(),
    state: str = Query(),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    connector_type, redirect_uri, _ = _config(kind)
    state_record = consume_oauth_state(db, state, purpose=f"connector:{kind}")
    if state_record.user_id is None: raise HTTPException(status_code=400, detail="OAuth state is not user-bound")
    tokens = exchange_google_code(code, redirect_uri)
    connector = db.scalar(select(Connector).where(Connector.owner_id == state_record.user_id, Connector.connector_type == connector_type, Connector.revoked_at.is_(None)))
    if connector is None:
        connector = Connector(id=str(uuid.uuid4()), owner_id=state_record.user_id, connector_type=connector_type, provider="google", name=kind.replace("-", " ").title(), status="active", authentication_status="authorized", scopes=tokens.get("scope"))
        db.add(connector); db.flush()
    credential = db.scalar(select(ConnectorCredential).where(ConnectorCredential.connector_id == connector.id))
    if credential is None: credential = ConnectorCredential(connector_id=connector.id); db.add(credential)
    credential.encrypted_access_token = encrypt_token(tokens["access_token"]) if tokens.get("access_token") else None
    credential.encrypted_refresh_token = encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else credential.encrypted_refresh_token
    credential.token_expires_at = expiry_from_response(tokens)
    connector.scopes = tokens.get("scope", connector.scopes); connector.status = "syncing"; connector.authentication_status = "authorized"
    db.commit()
    queue_initial_sync(background_tasks, connector)
    return RedirectResponse(settings.FRONTEND_URL)


@router.get("/{kind}/status")
def connector_status(kind: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> dict:
    connector_type, _, _ = _config(kind)
    connector = db.scalar(select(Connector).where(Connector.owner_id == current_user.id, Connector.connector_type == connector_type, Connector.revoked_at.is_(None)))
    return {"connected": connector is not None, "status": connector.status if connector else "disconnected", "scopes": connector.scopes if connector else None}


@router.post("/{kind}/disconnect", status_code=204)
def disconnect(kind: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> None:
    connector_type, _, _ = _config(kind)
    connector = db.scalar(select(Connector).where(Connector.owner_id == current_user.id, Connector.connector_type == connector_type, Connector.revoked_at.is_(None)))
    if connector is None: raise HTTPException(status_code=404, detail="Connector not found")
    connector.status = "revoked"; connector.revoked_at = datetime.now(timezone.utc); connector.authentication_status = "revoked"
    credential = db.scalar(select(ConnectorCredential).where(ConnectorCredential.connector_id == connector.id))
    if credential: credential.encrypted_access_token = None; credential.encrypted_refresh_token = None
    db.commit()
