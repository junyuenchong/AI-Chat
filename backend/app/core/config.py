"""
Application configuration.

Typed settings loaded from environment variables and `.env`.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# ────────────────────────────────────────────────────────
# Settings
# Internal — typed settings from environment and `.env`.
# Central configuration for database, auth, LLM, and rate limits.
# ────────────────────────────────────────────────────────
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

    redis_url: str = "redis://localhost:6379/0"

    # Empty GEMINI_API_KEY → demo streaming so compose works offline.
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_embedding_model: str = "text-embedding-3-small"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_model: str = ""
    gemini_embedding_model: str = "gemini-embedding-2"

    # Transient LLM/embedding failures: retry with exponential backoff before failover.
    llm_retry_max_attempts: int = 3
    llm_retry_base_delay_seconds: float = 0.5
    llm_retry_max_delay_seconds: float = 8.0

    # When use_rag is on, refuse instead of falling back to general LLM knowledge.
    rag_strict_mode: bool = False
    # Max pgvector cosine distance for a relevant chunk (0=identical, ~0.5=similar).
    rag_max_distance: float = 0.45

    # Set JWT_SECRET_KEY in production (min 32 bytes for HS256).
    jwt_secret_key: str = "change-me-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    rate_limit_per_minute: int = 30
    rate_limit_ip_per_minute: int = 120

    session_cookie_name: str = "session_id"
    cookie_samesite: str = "lax"

    # ────────────────────────────────────────────────────────
    # cookie_secure
    # Internal — derive Secure flag from app_env.
    # True in production so cookies are only sent over HTTPS.
    # ────────────────────────────────────────────────────────
    @property
    def cookie_secure(self) -> bool:
        # Only send session cookies over HTTPS in production deployments.
        return self.app_env == "production"

    # ────────────────────────────────────────────────────────
    # cors_origin_list
    # Internal — parse comma-separated CORS origins.
    # Returns a trimmed list for middleware and FastAPI CORS config.
    # ────────────────────────────────────────────────────────
    @property
    def cors_origin_list(self) -> list[str]:
        # Split the comma-separated env string and drop empty entries.
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    # ────────────────────────────────────────────────────────
    # llm_enabled
    # Internal — check whether any LLM API key is configured.
    # False when both Gemini and OpenAI keys are empty (demo mode).
    # ────────────────────────────────────────────────────────
    @property
    def llm_enabled(self) -> bool:
        """True when Gemini or OpenAI API key is configured."""
        # At least one provider key must be non-empty to enable real LLM calls.
        return bool(self.gemini_api_key.strip() or self.openai_api_key.strip())

    # ────────────────────────────────────────────────────────
    # llm_provider
    # Internal — resolve active LLM provider from configured keys.
    # Gemini wins if both keys are set; neither key → demo.
    # ────────────────────────────────────────────────────────
    @property
    def llm_provider(self) -> str:
        """Resolve provider: Gemini wins if both keys are set; neither → demo."""
        if self.gemini_api_key.strip():
            return "gemini"
        if self.openai_api_key.strip():
            return "openai"
        return "demo"  # No keys configured — use canned demo responses.


# ────────────────────────────────────────────────────────
# get_settings
# Internal — cached settings singleton.
# Loads and memoizes Settings from the environment on first call.
# ────────────────────────────────────────────────────────
@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings from the environment."""
    # Parsed once per process — env changes require a restart to take effect.
    return Settings()
