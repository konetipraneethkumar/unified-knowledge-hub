"""Google OAuth/OIDC adapter shared by identity and connector authorization."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from cryptography.fernet import Fernet
import jwt
from fastapi import HTTPException

from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


def authorization_url(*, redirect_uri: str, scope: str, state: str) -> str:
    return f"{GOOGLE_AUTH_URL}?{urlencode({'client_id': settings.GOOGLE_CLIENT_ID, 'redirect_uri': redirect_uri, 'response_type': 'code', 'access_type': 'offline', 'prompt': 'consent', 'scope': scope, 'state': state})}"


def exchange_google_code(code: str, redirect_uri: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_SECRET is None:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    body = urlencode({"code": code, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET.get_secret_value(), "redirect_uri": redirect_uri, "grant_type": "authorization_code"}).encode()
    try:
        with urlopen(Request(GOOGLE_TOKEN_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=15) as response:
            return json.loads(response.read())
    except Exception as error:
        raise HTTPException(status_code=400, detail="Google authorization exchange failed") from error


def refresh_google_token(refresh_token: str) -> dict:
    if settings.GOOGLE_CLIENT_SECRET is None: raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    body = urlencode({"refresh_token": refresh_token, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET.get_secret_value(), "grant_type": "refresh_token"}).encode()
    with urlopen(Request(GOOGLE_TOKEN_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=15) as response:
        return json.loads(response.read())


def validate_google_id_token(id_token: str, *, nonce: str | None) -> dict:
    try:
        key = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs").get_signing_key_from_jwt(id_token).key
        claims = jwt.decode(id_token, key, algorithms=["RS256"], audience=settings.GOOGLE_CLIENT_ID, issuer=list(GOOGLE_ISSUERS))
        if nonce is not None and claims.get("nonce") != nonce: raise ValueError("nonce mismatch")
        if not claims.get("sub"): raise ValueError("missing subject")
        return claims
    except Exception as error:
        raise HTTPException(status_code=400, detail="Invalid Google ID token") from error


def encrypt_token(token: str) -> str:
    return Fernet(settings.CONNECTOR_TOKEN_ENCRYPTION_KEY.get_secret_value().encode()).encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
    return Fernet(settings.CONNECTOR_TOKEN_ENCRYPTION_KEY.get_secret_value().encode()).decrypt(token.encode()).decode()


def expiry_from_response(tokens: dict) -> datetime | None:
    seconds = tokens.get("expires_in")
    return datetime.now(timezone.utc) + timedelta(seconds=int(seconds)) if seconds else None
