"""
LangChain LLM.

Connect to the language model and embeddings.
Used by agent.py for replies and by retrieval.py for RAG vectors.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.core.config import Settings, get_settings
from app.domain.chat.entities import ChatMessage
from app.domain.chat.ports import LLMPort
from app.infrastructure.ai.langchain.prompts import (
    SUMMARIZE_SYSTEM_PROMPT,
    SUMMARIZE_USER_PROMPT,
    SYSTEM_PROMPT,
    append_rag_context,
)
from app.shared.retry import backoff_delay, is_retryable_error, retry_async
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# Map our role names to LangChain message classes.
_ROLE_TO_LC: dict[str, Callable[[str], BaseMessage]] = {
    "system": SystemMessage,
    "assistant": AIMessage,
    "user": HumanMessage,
}


class LLMProviderError(Exception):
    """Upstream model failure (mapped to domain/API errors in application)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "LLM_PROVIDER_ERROR",
        user_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.user_message = (
            user_message or "The language model failed. Please try again."
        )

    # ────────────────────────────────────────────────────────
    # from_exception
    # Internal — langchain / llm
    # Maps raw provider errors to user-friendly messages.
    # ────────────────────────────────────────────────────────
    @classmethod
    def from_exception(cls, exc: Exception | None) -> LLMProviderError:
        """Build a typed error from an upstream exception."""
        if exc is None:
            return cls("All configured LLM providers failed.")
        message = str(exc).lower()
        if "permission_denied" in message or "denied access" in message:
            return cls(
                str(exc),
                code="LLM_PERMISSION_DENIED",
                user_message=(
                    "Gemini API access is denied for this Google Cloud project. "
                    "Enable billing and the Gemini API on the project for your key, "
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


# ────────────────────────────────────────────────────────
# _build_openai_chat_model
# Internal — langchain / llm
# Creates the OpenAI ChatOpenAI client from settings.
# ────────────────────────────────────────────────────────
def _build_openai_chat_model(settings: Settings) -> Any:
    """Build OpenAI chat model."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.4,
        streaming=True,
    )


# ────────────────────────────────────────────────────────
# _build_gemini_chat_model
# Internal — langchain / llm
# Creates the Gemini ChatGoogleGenerativeAI client from settings.
# ────────────────────────────────────────────────────────
def _build_gemini_chat_model(settings: Settings, *, model: str | None = None) -> Any:
    """Build Gemini chat model."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.4,
        streaming=True,
    )


# ────────────────────────────────────────────────────────
# _build_openai_embeddings
# Internal — langchain / llm
# Creates the OpenAI embedding client used by retrieval.py.
# ────────────────────────────────────────────────────────
def _build_openai_embeddings(settings: Settings) -> Any:
    """Build OpenAI embeddings client."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.llm_embedding_model,
        api_key=settings.openai_api_key,
    )


# ────────────────────────────────────────────────────────
# _build_gemini_embeddings
# Internal — langchain / llm
# Creates the Gemini embedding client used by retrieval.py.
# ────────────────────────────────────────────────────────
def _build_gemini_embeddings(settings: Settings) -> Any:
    """Build Gemini embeddings client."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        google_api_key=settings.gemini_api_key,
    )


# ────────────────────────────────────────────────────────
# to_lc_messages
# Internal — langchain / llm
# Converts our dict messages to LangChain message objects.
# ────────────────────────────────────────────────────────
def to_lc_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    """Convert ChatMessage dicts to LangChain BaseMessage list."""
    lc: list[BaseMessage] = []
    for msg in messages:
        role, content = msg["role"], msg["content"]
        if role in _ROLE_TO_LC:
            lc.append(_ROLE_TO_LC[role](content))
        else:
            lc.append(HumanMessage(content))
    return lc


# ────────────────────────────────────────────────────────
# _parse_stream_chunk
# Internal — langchain / llm
# Extracts plain text from one streamed LLM chunk.
# ────────────────────────────────────────────────────────
def _parse_stream_chunk(content: object) -> str:
    """Parse one stream chunk into a text string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(_parse_chunk_part(part) for part in content)
    return ""


# ────────────────────────────────────────────────────────
# _parse_chunk_part
# Internal — langchain / llm
# Handles nested chunk shapes (string or {type: text}).
# ────────────────────────────────────────────────────────
def _parse_chunk_part(part: object) -> str:
    """Parse one part of a multi-part stream chunk."""
    if isinstance(part, str):
        return part
    if isinstance(part, dict) and part.get("type") == "text":
        return str(part.get("text", ""))
    return ""


# ────────────────────────────────────────────────────────
# build_chat_model
# Internal — langchain / llm
# Builds the primary chat model from settings.
# ────────────────────────────────────────────────────────
def build_chat_model(settings: Settings) -> Any | None:
    """Return the primary LangChain chat model, or None when disabled."""
    if not settings.llm_enabled:
        return None
    builder = _CHAT_BUILDERS.get(settings.llm_provider)
    if builder is None:
        return None
    try:
        return builder(settings)
    except Exception:
        return None


# ────────────────────────────────────────────────────────
# build_chat_model_chain
# Internal — langchain / llm
# Builds primary + fallback models for resilient LLM calls.
# ────────────────────────────────────────────────────────
def build_chat_model_chain(settings: Settings) -> list[tuple[str, Any]]:
    """Return ordered (label, model) pairs — primary first, then fallbacks."""
    chain: list[tuple[str, Any]] = []
    if not settings.llm_enabled:
        return chain

    # Step 1: add the configured primary provider.
    primary = build_chat_model(settings)
    if primary is not None:
        chain.append((settings.llm_provider, primary))

    # Step 2: add Gemini fallback model when configured.
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

    # Step 3: add OpenAI as cross-provider fallback when a key exists.
    if settings.openai_api_key.strip() and settings.llm_provider != "openai":
        try:
            chain.append(("openai", _build_openai_chat_model(settings)))
        except Exception:
            pass

    return chain


_CHAT_BUILDERS: dict[str, Callable[[Settings], Any]] = {
    "gemini": _build_gemini_chat_model,
    "openai": _build_openai_chat_model,
}


class LangChainLLM:
    """LLMPort — LangChain astream / ainvoke with per-model retry + fallback chain."""

    def __init__(self, model_chain: list[tuple[str, Any]]) -> None:
        if not model_chain:
            raise ValueError("LangChainLLM requires at least one model.")
        self._model_chain = model_chain

    def _retry_settings(self) -> tuple[int, float, float]:
        cfg = get_settings()
        return (
            cfg.llm_retry_max_attempts,
            cfg.llm_retry_base_delay_seconds,
            cfg.llm_retry_max_delay_seconds,
        )

    # ────────────────────────────────────────────────────────
    # stream
    # Endpoint: POST /chat/stream (internal)
    # Yields AI reply tokens one at a time for live streaming.
    # ────────────────────────────────────────────────────────
    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        """Stream reply tokens — retries transient errors, then tries next model."""
        lc_messages = to_lc_messages(messages)
        max_attempts, base_delay, max_delay = self._retry_settings()
        last_exc: Exception | None = None
        for label, llm in self._model_chain:
            for attempt in range(max_attempts):
                yielded_any = False
                try:
                    async for chunk in llm.astream(lc_messages):
                        text = _parse_stream_chunk(chunk.content)
                        if text:
                            yielded_any = True
                            yield text
                    return
                except Exception as exc:
                    logger.warning(
                        "LLM stream failed for %s (attempt %s/%s)",
                        label,
                        attempt + 1,
                        max_attempts,
                        exc_info=exc,
                    )
                    last_exc = exc
                    if yielded_any:
                        break
                    is_last_attempt = attempt >= max_attempts - 1
                    if is_last_attempt or not is_retryable_error(exc):
                        break
                    delay = backoff_delay(
                        attempt, base=base_delay, max_delay=max_delay
                    )
                    logger.warning(
                        "Retrying LLM stream for %s in %.2fs", label, delay
                    )
                    await asyncio.sleep(delay)
        raise LLMProviderError.from_exception(last_exc)

    # ────────────────────────────────────────────────────────
    # complete
    # Endpoint: POST /chat/complete (internal)
    # Returns the full AI reply in one call (non-streaming).
    # ────────────────────────────────────────────────────────
    async def complete(self, messages: list[ChatMessage]) -> str:
        """Return the full reply — retries transient errors, then tries next model."""
        lc_messages = to_lc_messages(messages)
        max_attempts, base_delay, max_delay = self._retry_settings()
        last_exc: Exception | None = None
        for label, llm in self._model_chain:
            try:

                async def _invoke(current_llm: Any = llm) -> str:
                    result = await current_llm.ainvoke(lc_messages)
                    content = result.content
                    return content if isinstance(content, str) else str(content)

                return await retry_async(
                    _invoke,
                    max_attempts=max_attempts,
                    base_delay=base_delay,
                    max_delay=max_delay,
                    label=f"LLM complete ({label})",
                )
            except Exception as exc:
                logger.warning("LLM complete failed for %s", label, exc_info=exc)
                last_exc = exc
        raise LLMProviderError.from_exception(last_exc)

    # ────────────────────────────────────────────────────────
    # summarize
    # Internal — ARQ background job
    # Shortens a conversation transcript into a brief title or summary.
    # ────────────────────────────────────────────────────────
    async def summarize(self, transcript: str) -> str:
        """Summarize a conversation transcript."""
        prompt = SUMMARIZE_USER_PROMPT.format(transcript=transcript[:8000])
        messages: list[ChatMessage] = [
            {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return await self.complete(messages)


# ────────────────────────────────────────────────────────
# demo_reply_text
# Internal — tests only
# Returns a demo reply without calling an external API.
# ────────────────────────────────────────────────────────
def demo_reply_text(user_message: str, rag_context: str | None) -> str:
    """Helper for tests — returns a demo reply without calling an API."""
    messages: list[ChatMessage] = [
        {"role": "system", "content": append_rag_context(SYSTEM_PROMPT, rag_context)},
        {"role": "user", "content": user_message},
    ]
    return DemoLLM._reply(messages)


class DemoLLM:
    """LLMPort for offline demo mode — no LangChain or external API calls."""

    @staticmethod
    def _reply(messages: list[ChatMessage]) -> str:
        user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        rag_context = system if "Retrieved context:" in system else None
        rag_note = (
            f"RAG context used:\n{rag_context[:500]}"
            if rag_context
            else "No RAG hits. Upload a document or ask about LangChain and RAG."
        )
        return (
            "Demo mode is on because GEMINI_API_KEY is empty. "
            "The HTTP path, PostgreSQL persistence, Redis rate limit, and SSE stream "
            "still run for real.\n\n"
            f"You said: {user_message[:300]}\n\n"
            "LangChain = AI components (LLM, prompts, embeddings). "
            "RAG = Retriever + Knowledge chunks + LLM.\n\n"
            f"{rag_note}"
        )

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        text = self._reply(messages)
        for word in text.split(" "):
            yield word + " "
            await asyncio.sleep(0.02)

    async def complete(self, messages: list[ChatMessage]) -> str:
        return self._reply(messages).strip()

    async def summarize(self, transcript: str) -> str:
        compact = " ".join(transcript.split())
        return f"Demo summary: {compact[:280]}"


# ────────────────────────────────────────────────────────
# build_llm_port
# Internal — langchain / llm
# Entry point — returns DemoLLM or LangChainLLM based on settings.
# ────────────────────────────────────────────────────────
def build_llm_port(settings: Settings | None = None) -> LLMPort:
    """Build the LLM port used by ChatAgent."""
    cfg = settings or get_settings()
    # No API key or LLM disabled — use offline demo replies.
    if not cfg.llm_enabled:
        return DemoLLM()
    chain = build_chat_model_chain(cfg)
    if not chain:
        return DemoLLM()
    return LangChainLLM(chain)


_EMBEDDING_BUILDERS: dict[str, Callable[[Settings], Any]] = {
    "gemini": _build_gemini_embeddings,
    "openai": _build_openai_embeddings,
}


# ────────────────────────────────────────────────────────
# get_embeddings
# Internal — langchain / llm
# Returns the embedding client used by retrieval.py for RAG.
# ────────────────────────────────────────────────────────
def get_embeddings(settings: Settings | None = None) -> Any | None:
    """Return the embedding client for the configured provider."""
    cfg = settings or get_settings()
    if not cfg.llm_enabled:
        return None
    builder = _EMBEDDING_BUILDERS.get(cfg.llm_provider)
    if builder is None:
        return None
    try:
        return builder(cfg)
    except Exception:
        return None
