"""
LangChain chat model factories.

Request path:
  infrastructure/ai/langchain/llm/provider.py (build_llm_port)
    → infrastructure/ai/langchain/llm/factory.py  (this file)
    → langchain_google_genai / langchain_openai
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.config import Settings

_CHAT_BUILDERS: dict[str, Callable[[Settings], Any]] = {}


# ────────────────────────────────────────────────────────
# _build_openai_chat_model
# Path: infrastructure/ai/langchain/llm/factory.py
# Internal — registered in _CHAT_BUILDERS for provider "openai".
# Use: create a streaming ChatOpenAI instance from Settings.
# ────────────────────────────────────────────────────────
def _build_openai_chat_model(settings: Settings) -> Any:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.4,
        streaming=True,
    )


# ────────────────────────────────────────────────────────
# _build_gemini_chat_model
# Path: infrastructure/ai/langchain/llm/factory.py
# Internal — registered in _CHAT_BUILDERS for provider "gemini".
# Use: create a streaming ChatGoogleGenerativeAI instance from Settings.
# ────────────────────────────────────────────────────────
def _build_gemini_chat_model(settings: Settings, *, model: str | None = None) -> Any:
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.4,
        streaming=True,
    )


_CHAT_BUILDERS.update(
    {
        "gemini": _build_gemini_chat_model,
        "openai": _build_openai_chat_model,
    }
)


# ────────────────────────────────────────────────────────
# build_chat_model
# Path: infrastructure/ai/langchain/llm/factory.py
# Internal — called by build_chat_model_chain().
# Use: build the primary LangChain model for the configured provider.
# ────────────────────────────────────────────────────────
def build_chat_model(settings: Settings) -> Any | None:
    # Step 1 — no API keys → no model.
    if not settings.llm_enabled:
        return None
    # Step 2 — look up the builder for gemini or openai.
    builder = _CHAT_BUILDERS.get(settings.llm_provider)
    if builder is None:
        return None
    # Step 3 — instantiate; return None if the SDK import or init fails.
    try:
        return builder(settings)
    except Exception:
        return None


# ────────────────────────────────────────────────────────
# build_chat_model_chain
# Path: infrastructure/ai/langchain/llm/factory.py
# Internal — called by build_llm_port().
# Use: build an ordered fallback chain: primary → gemini fallback → openai.
# ────────────────────────────────────────────────────────
def build_chat_model_chain(settings: Settings) -> list[tuple[str, Any]]:
    chain: list[tuple[str, Any]] = []
    if not settings.llm_enabled:
        return chain

    # Step 1 — add the primary model (gemini or openai from Settings).
    primary = build_chat_model(settings)
    if primary is not None:
        chain.append((settings.llm_provider, primary))

    # Step 2 — optionally add a secondary Gemini model as fallback.
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
                    _build_gemini_chat_model(settings, model=fallback_model),
                )
            )
        except Exception:
            pass

    # Step 3 — optionally add OpenAI as a last resort when primary is Gemini.
    if settings.openai_api_key.strip() and settings.llm_provider != "openai":
        try:
            chain.append(("openai", _build_openai_chat_model(settings)))
        except Exception:
            pass

    return chain
