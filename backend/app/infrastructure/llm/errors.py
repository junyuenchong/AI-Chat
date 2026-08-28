"""
LLM infrastructure errors.

Raised by LangChain adapters; mapped to domain/API errors in the application layer.
"""

from __future__ import annotations


class LLMProviderError(Exception):
    """Upstream model failure from an LLM adapter (not a user-facing chat token)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "LLM_PROVIDER_ERROR",
        user_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.user_message = user_message or "The language model failed. Please try again."

    @classmethod
    def from_exception(cls, exc: Exception | None) -> LLMProviderError:
        if exc is None:
            return cls("All configured LLM providers failed.")
        message = str(exc).lower()
        if "permission_denied" in message or "denied access" in message:
            return cls(
                str(exc),
                code="LLM_PERMISSION_DENIED",
                user_message=(
                    "Gemini API access is denied for this Google Cloud project. "
                    "Enable billing and the Gemini API on the project linked to your key, "
                    "or use demo mode (empty GEMINI_API_KEY)."
                ),
            )
        if "quota" in message or "429" in message:
            return cls(
                str(exc),
                code="LLM_QUOTA_EXCEEDED",
                user_message=(
                    "Gemini API quota exceeded for this project. "
                    "Check billing and rate limits in Google AI Studio, then try again."
                ),
            )
        if "not_found" in message or "no longer available" in message:
            return cls(
                str(exc),
                code="LLM_MODEL_NOT_FOUND",
                user_message=(
                    "The configured Gemini model is unavailable. "
                    "Set GEMINI_MODEL=gemini-3.6-flash in .env and restart the API."
                ),
            )
        return cls(str(exc))
