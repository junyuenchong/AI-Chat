"""
LangChain LLM port — streaming, complete, and demo mode.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import Settings, get_settings
from app.domain.chat.entities import ChatMessage
from app.domain.chat.ports import LLMPort
from app.infrastructure.ai.langchain.llm.factory import build_chat_model_chain
from app.infrastructure.ai.langchain.llm.messages import parse_stream_chunk, to_lc_messages
from app.infrastructure.ai.langchain.prompts import SYSTEM_PROMPT
from app.shared.retry import backoff_delay, is_retryable_error, retry_async

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Upstream model failure (mapped to domain/API errors in application)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Internal — raised by LangChainLLM on provider failure.
    # Use: carry a user-facing message for ChatService / SSE error events.
    # ────────────────────────────────────────────────────────
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
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Internal — called when all models in the chain fail.
    # Use: map raw upstream errors to typed codes and friendly messages.
    # ────────────────────────────────────────────────────────
    @classmethod
    def from_exception(cls, exc: Exception | None) -> LLMProviderError:
        """Build a typed error from an upstream exception."""
        if exc is None:
            return cls("All configured LLM providers failed.")
        message = str(exc).lower()
        # Step 1 — detect permission / billing errors.
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
        # Step 2 — detect quota / rate-limit errors.
        if "quota" in message or "429" in message:
            return cls(
                str(exc),
                code="LLM_QUOTA_EXCEEDED",
                user_message=(
                    "Gemini API quota exceeded for this project. "
                    "Check billing and rate limits in Google AI Studio, then try again."
                ),
            )
        # Step 3 — detect deprecated or missing model errors.
        if "not_found" in message or "no longer available" in message:
            return cls(
                str(exc),
                code="LLM_MODEL_NOT_FOUND",
                user_message=(
                    "The configured Gemini model is unavailable. "
                    "Set GEMINI_MODEL=gemini-3.6-flash in .env and restart the API."
                ),
            )
        # Step 4 — fall back to a generic provider error.
        return cls(str(exc))


class LangChainLLM:
    """LLMPort — LangChain astream / ainvoke with per-model retry + fallback chain."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Internal — created by build_llm_port().
    # Use: store the ordered list of (label, LangChain model) pairs to try.
    # ────────────────────────────────────────────────────────
    def __init__(self, model_chain: list[tuple[str, Any]]) -> None:
        if not model_chain:
            raise ValueError("LangChainLLM requires at least one model.")
        self._model_chain = model_chain

    # ────────────────────────────────────────────────────────
    # _retry_settings
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Internal — read retry config from Settings.
    # Use: share max attempts and backoff values across stream/complete.
    # ────────────────────────────────────────────────────────
    def _retry_settings(self) -> tuple[int, float, float]:
        cfg = get_settings()
        return (
            cfg.llm_retry_max_attempts,
            cfg.llm_retry_base_delay_seconds,
            cfg.llm_retry_max_delay_seconds,
        )

    # ────────────────────────────────────────────────────────
    # stream
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Endpoint: POST /chat/stream (via ChatChain → stream_llm_tokens)
    # Use: yield reply tokens one at a time for SSE streaming.
    # ────────────────────────────────────────────────────────
    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        """Stream reply tokens — retries transient errors, then tries next model."""
        # Step 1 — convert domain messages to LangChain message objects.
        lc_messages = to_lc_messages(messages)
        max_attempts, base_delay, max_delay = self._retry_settings()
        last_exc: Exception | None = None
        # Step 2 — try each model in the fallback chain.
        for label, llm in self._model_chain:
            for attempt in range(max_attempts):
                yielded_any = False
                try:
                    # Step 3 — stream chunks from the current model.
                    async for chunk in llm.astream(lc_messages):
                        text = parse_stream_chunk(chunk.content)
                        if text:
                            yielded_any = True
                            yield text
                    # Step 4 — success; stop trying other models.
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
                    # Step 5 — cannot retry after tokens were already sent.
                    if yielded_any:
                        break
                    is_last_attempt = attempt >= max_attempts - 1
                    if is_last_attempt or not is_retryable_error(exc):
                        break
                    # Step 6 — wait with exponential backoff, then retry.
                    delay = backoff_delay(
                        attempt, base=base_delay, max_delay=max_delay
                    )
                    logger.warning(
                        "Retrying LLM stream for %s in %.2fs", label, delay
                    )
                    await asyncio.sleep(delay)
        # Step 7 — all models failed; raise a typed provider error.
        raise LLMProviderError.from_exception(last_exc)

    # ────────────────────────────────────────────────────────
    # complete
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Endpoint: POST /chat/complete (via ChatChain)
    # Use: return the full assistant reply in one call (no streaming).
    # ────────────────────────────────────────────────────────
    async def complete(self, messages: list[ChatMessage]) -> str:
        """Return the full reply — retries transient errors, then tries next model."""
        # Step 1 — convert domain messages to LangChain message objects.
        lc_messages = to_lc_messages(messages)
        max_attempts, base_delay, max_delay = self._retry_settings()
        last_exc: Exception | None = None
        # Step 2 — try each model in the fallback chain.
        for label, llm in self._model_chain:
            try:

                async def _invoke(current_llm: Any = llm) -> str:
                    result = await current_llm.ainvoke(lc_messages)
                    content = result.content
                    return content if isinstance(content, str) else str(content)

                # Step 3 — invoke with retry_async (handles backoff internally).
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
        # Step 4 — all models failed; raise a typed provider error.
        raise LLMProviderError.from_exception(last_exc)


def demo_reply_text(user_message: str) -> str:
    """Helper for tests — returns a demo reply without calling an API."""
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return DemoLLM._reply(messages)


class DemoLLM:
    """LLMPort for offline demo mode — no LangChain or external API calls."""

    # ────────────────────────────────────────────────────────
    # _reply
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Internal — shared by DemoLLM.stream and DemoLLM.complete.
    # Use: build the canned demo-mode response text.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _reply(messages: list[ChatMessage]) -> str:
        # Step 1 — find the latest user message in the list.
        user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        # Step 2 — return a canned reply that echoes the user input.
        return (
            "Demo mode is on because GEMINI_API_KEY is empty. "
            "The HTTP path, PostgreSQL persistence, and SSE stream still run for real.\n\n"
            f"You said: {user_message[:300]}\n\n"
            "This is a Question 2 chat stack: FastAPI streams tokens, "
            "Postgres stores history, LangChain formats messages and calls the LLM."
        )

    # ────────────────────────────────────────────────────────
    # stream
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Endpoint: POST /chat/stream (demo mode)
    # Use: simulate token streaming by yielding words with a short delay.
    # ────────────────────────────────────────────────────────
    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        # Step 1 — build the full reply text.
        text = self._reply(messages)
        # Step 2 — yield one word at a time to mimic real SSE streaming.
        for word in text.split(" "):
            yield word + " "
            await asyncio.sleep(0.02)

    # ────────────────────────────────────────────────────────
    # complete
    # Path: infrastructure/ai/langchain/llm/provider.py
    # Endpoint: POST /chat/complete (demo mode)
    # Use: return the full demo reply in one shot.
    # ────────────────────────────────────────────────────────
    async def complete(self, messages: list[ChatMessage]) -> str:
        return self._reply(messages).strip()


def build_llm_port(settings: Settings | None = None) -> LLMPort:
    """Build the LLM port used by ChatChain."""
    cfg = settings or get_settings()
    # Step 1 — no API keys configured → demo mode.
    if not cfg.llm_enabled:
        return DemoLLM()
    # Step 2 — build the model fallback chain from factory.
    chain = build_chat_model_chain(cfg)
    if not chain:
        return DemoLLM()
    # Step 3 — wrap the chain in LangChainLLM (retry + failover).
    return LangChainLLM(chain)
