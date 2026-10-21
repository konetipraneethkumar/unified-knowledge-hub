from pathlib import Path

from pydantic import SecretStr
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: SecretStr = SecretStr("development-only-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CONNECTOR_TOKEN_ENCRYPTION_KEY: SecretStr = SecretStr("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    FRONTEND_URL: str = "http://localhost:5173"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: SecretStr | None = None
    GOOGLE_AUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    GOOGLE_DRIVE_REDIRECT_URI: str = "http://localhost:8000/api/v1/connectors/google-drive/callback"
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/v1/connectors/gmail/callback"
    GOOGLE_CLASSROOM_REDIRECT_URI: str = "http://localhost:8000/api/v1/connectors/google-classroom/callback"
    LOCAL_STORAGE_ROOT: str | None = None
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_API_KEY: SecretStr | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_DIMENSIONS: int = 8
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: SecretStr | None = None
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_TEMPERATURE: float = Field(default=0.2, ge=0, le=2)
    LLM_TIMEOUT_SECONDS: float = Field(default=30, gt=0)
    RAG_TOP_K: int = Field(default=5, ge=1, le=100)
    PAIRING_CODE_TTL_MINUTES: int = 10
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        extra="ignore",
    )


settings = Settings()
