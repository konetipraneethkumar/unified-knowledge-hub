from datetime import datetime, timezone

from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, issue_user_token, password_hasher
from app.models import AuthToken, User
from app.schemas.auth import LoginRequest, RegisterRequest, SessionRead, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> SessionRead:
    email = request.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=email, password_hash=password_hasher.hash(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return SessionRead(access_token=issue_user_token(db, user), user=user)


@router.post("/login", response_model=SessionRead)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> SessionRead:
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    try:
        valid = user is not None and password_hasher.verify(user.password_hash, request.password)
    except VerifyMismatchError:
        valid = False
    if not valid or user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return SessionRead(access_token=issue_user_token(db, user), user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    # Revoke every active opaque token for the authenticated principal.
    now = datetime.now(timezone.utc)
    for token in db.scalars(select(AuthToken).where(AuthToken.user_id == current_user.id, AuthToken.revoked_at.is_(None))).all():
        token.revoked_at = now
    db.commit()


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
