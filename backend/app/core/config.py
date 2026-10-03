from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    DATABASE_URL: str
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_API_KEY: SecretStr | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_DIMENSIONS: int = 8
    SESSION_TOKEN_TTL_HOURS: int = 24
    PAIRING_CODE_TTL_MINUTES: int = 10
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:4173,http://127.0.0.1:4173"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
