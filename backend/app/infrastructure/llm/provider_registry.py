"""
LLM provider registry.

Strategy map for building chat models and embeddings by provider.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.config import Settings

# ────────────────────────────────────────────────────────

# _build_gemini_chat

# Internal — LLM provider

# Instantiates a streaming Gemini chat model from settings.


# ────────────────────────────────────────────────────────
def _build_gemini_chat(settings: Settings) -> Any:
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Wire Gemini model name, API key, and streaming from settings.

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.4,
        streaming=True,
    )


# ────────────────────────────────────────────────────────

# _build_gemini_chat_with_model

# Internal — LLM provider

# Instantiates a streaming Gemini chat model with an explicit model name.


# ────────────────────────────────────────────────────────
def _build_gemini_chat_with_model(settings: Settings, model: str) -> Any:
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.gemini_api_key,
        temperature=0.4,
        streaming=True,
    )


# ────────────────────────────────────────────────────────

# _build_openai_chat

# Internal — LLM provider

# Instantiates a streaming OpenAI chat model from settings.


# ────────────────────────────────────────────────────────
def _build_openai_chat(settings: Settings) -> Any:
    from langchain_openai import ChatOpenAI

    # Wire OpenAI model name, API key, and streaming from settings.

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.4,
        streaming=True,
    )


# ────────────────────────────────────────────────────────

# _build_gemini_embeddings

# Internal — LLM provider

# Instantiates a Gemini embeddings client from settings.


# ────────────────────────────────────────────────────────
def _build_gemini_embeddings(settings: Settings) -> Any:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        google_api_key=settings.gemini_api_key,
    )


# ────────────────────────────────────────────────────────

# _build_openai_embeddings

# Internal — LLM provider

# Instantiates an OpenAI embeddings client from settings.


# ────────────────────────────────────────────────────────
def _build_openai_embeddings(settings: Settings) -> Any:
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.llm_embedding_model,
        api_key=settings.openai_api_key,
    )


_CHAT_BUILDERS: dict[str, Callable[[Settings], Any]] = {
    "gemini": _build_gemini_chat,
    "openai": _build_openai_chat,
}

_EMBEDDING_BUILDERS: dict[str, Callable[[Settings], Any]] = {
    "gemini": _build_gemini_embeddings,
    "openai": _build_openai_embeddings,
}

# ────────────────────────────────────────────────────────

# _safe_build

# Internal — LLM provider

# Resolves the provider builder and returns None on misconfiguration.


# ────────────────────────────────────────────────────────
def _safe_build(
    settings: Settings,
    builders: dict[str, Callable[[Settings], Any]],
) -> Any | None:

    # LLM disabled in config — skip building any client.

    if not settings.llm_enabled:
        return None

    # Look up the builder for the configured provider name.

    builder = builders.get(settings.llm_provider)
    if builder is None:
        return None
    try:
        # Instantiate the client; swallow misconfiguration errors.

        return builder(settings)
    except Exception:
        return None


# ────────────────────────────────────────────────────────

# build_chat_model

# Internal — LLM provider

# Returns the configured chat model, or None when LLM is disabled.


# ────────────────────────────────────────────────────────
def build_chat_model(settings: Settings) -> Any | None:

    # Delegate to the shared safe-build helper for chat models.

    return _safe_build(settings, _CHAT_BUILDERS)


# ────────────────────────────────────────────────────────

# build_chat_model_chain

# Internal — LLM provider

# Returns ordered (label, model) pairs: primary then stream fallbacks.


# ────────────────────────────────────────────────────────
def build_chat_model_chain(settings: Settings) -> list[tuple[str, Any]]:
    """
    Primary model plus stream fallbacks for production resilience.

    Order:
      1. Configured primary provider (Gemini or OpenAI)
      2. Alternate Gemini model (GEMINI_FALLBACK_MODEL), when set
      3. Cross-provider OpenAI, when key is configured and primary is not OpenAI
    """
    chain: list[tuple[str, Any]] = []

    if not settings.llm_enabled:
        return chain

    primary = build_chat_model(settings)
    if primary is not None:
        chain.append((settings.llm_provider, primary))

    fallback_model = settings.gemini_fallback_model.strip()
    if (
        fallback_model
        and settings.gemini_api_key.strip()
        and fallback_model != settings.gemini_model
    ):
        try:
            chain.append(
                (
                    f"gemini:{fallback_model}",
                    _build_gemini_chat_with_model(settings, fallback_model),
                )
            )
        except Exception:
            pass

    if settings.openai_api_key.strip() and settings.llm_provider != "openai":
        try:
            chain.append(("openai", _build_openai_chat(settings)))
        except Exception:
            pass

    return chain


# ────────────────────────────────────────────────────────

# build_embeddings

# Internal — LLM provider

# Returns the configured embeddings client, or None when LLM is disabled.


# ────────────────────────────────────────────────────────
def build_embeddings(settings: Settings) -> Any | None:

    # Delegate to the shared safe-build helper for embeddings clients.

    return _safe_build(settings, _EMBEDDING_BUILDERS)
