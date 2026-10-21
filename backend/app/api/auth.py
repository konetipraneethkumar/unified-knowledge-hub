from datetime import datetime, timezone
from urllib.parse import urlencode
import secrets

from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import consume_oauth_state, create_oauth_state, get_current_active_user, issue_access_token, issue_refresh_token, password_hasher, rotate_refresh_token
from app.models import OAuthAccount, RefreshToken, User
from app.schemas.auth import LoginRequest, ProfileUpdateRequest, RefreshRequest, RegisterRequest, SessionRead, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _session(db: Session, user: User) -> SessionRead:
    return SessionRead(access_token=issue_access_token(user), refresh_token=issue_refresh_token(db, user), user=user)


@router.post("/register", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> SessionRead:
    email = request.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=email, password_hash=password_hasher.hash(request.password), display_name=request.display_name, is_active=True)
    db.add(user); db.commit(); db.refresh(user)
    return _session(db, user)


@router.post("/login", response_model=SessionRead)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> SessionRead:
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    try:
        valid = user is not None and user.password_hash is not None and password_hasher.verify(user.password_hash, request.password)
    except VerifyMismatchError:
        valid = False
    if not valid or user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _session(db, user)


@router.post("/refresh", response_model=SessionRead)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)) -> SessionRead:
    user, refresh_token = rotate_refresh_token(db, request.refresh_token)
    return SessionRead(access_token=issue_access_token(user), refresh_token=refresh_token, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> None:
    now = datetime.now(timezone.utc)
    for token in db.scalars(select(RefreshToken).where(RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None))).all(): token.revoked_at = now
    db.commit()


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_active_user)) -> User: return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    current_user.display_name = request.display_name.strip() if request.display_name else None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/google/login")
def google_login(db: Session = Depends(get_db)) -> RedirectResponse:
    if not settings.GOOGLE_CLIENT_ID: raise HTTPException(status_code=503, detail="Google login is not configured")
    nonce = secrets.token_urlsafe(24)
    state = create_oauth_state(db, user_id=None, purpose="google_login", nonce=nonce)
    query = urlencode({"client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": settings.GOOGLE_AUTH_REDIRECT_URI, "response_type": "code", "scope": "openid email profile", "state": state, "nonce": nonce})
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
def google_callback(code: str = Query(), state: str = Query(), db: Session = Depends(get_db)) -> RedirectResponse:
    from app.connectors.google import exchange_google_code, validate_google_id_token
    record = consume_oauth_state(db, state, purpose="google_login")
    tokens = exchange_google_code(code, settings.GOOGLE_AUTH_REDIRECT_URI)
    claims = validate_google_id_token(tokens["id_token"], nonce=record.nonce)
    account = db.scalar(select(OAuthAccount).where(OAuthAccount.provider == "google", OAuthAccount.provider_subject == claims["sub"]))
    if account is None:
        user = User(email=claims.get("email", f"google-{claims['sub']}@invalid"), display_name=claims.get("name"), avatar_url=claims.get("picture"), is_verified=bool(claims.get("email_verified")), is_active=True)
        db.add(user); db.flush(); db.add(OAuthAccount(user_id=user.id, provider="google", provider_subject=claims["sub"], email_at_link_time=claims.get("email"))); db.commit()
    else: user = db.get(User, account.user_id)
    if user is None or not user.is_active: raise HTTPException(status_code=403, detail="Inactive account")
    result = _session(db, user)
    return RedirectResponse(f"{settings.FRONTEND_URL}?{urlencode({'access_token': result.access_token, 'refresh_token': result.refresh_token})}")
