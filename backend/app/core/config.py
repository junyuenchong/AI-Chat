"""
Application configuration.

Typed settings loaded from environment variables and `.env`.
"""

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
    database_url: str = (
        "postgresql+asyncpg://ai_chat:ai_chat_pass@localhost:5432/ai_chat"
    )

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_model: str = ""

    llm_retry_max_attempts: int = 3
    llm_retry_base_delay_seconds: float = 0.5
    llm_retry_max_delay_seconds: float = 8.0

    jwt_secret_key: str = "change-me-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

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
    return Settings()
