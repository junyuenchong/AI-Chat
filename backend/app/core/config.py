"""Environment-backed settings — Docker, local, and tests share one schema."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings from environment / `.env`. Never commit real API keys."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Chat"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    postgres_user: str = "ai_chat"
    postgres_password: str = "ai_chat_pass"
    postgres_db: str = "ai_chat"
    database_url: str = "postgresql+asyncpg://ai_chat:ai_chat_pass@localhost:5432/ai_chat"

    redis_url: str = "redis://localhost:6379/0"

    # Empty GEMINI_API_KEY → demo streaming so compose works offline.
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_embedding_model: str = "text-embedding-3-small"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_embedding_model: str = "models/text-embedding-004"

    # Override JWT_SECRET_KEY in any shared or production environment.
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    rate_limit_per_minute: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # ---------------------------------------------------------------------------
    # Provider pick — Gemini wins if both keys are set; neither → "demo".
    # ---------------------------------------------------------------------------
    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip() or self.openai_api_key.strip())

    @property
    def llm_provider(self) -> str:
        if self.gemini_api_key.strip():
            return "gemini"
        if self.openai_api_key.strip():
            return "openai"
        return "demo"


@lru_cache
def get_settings() -> Settings:
    # Cache so every request does not re-parse the environment.
    return Settings()
