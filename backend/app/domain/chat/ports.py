"""
Chat domain ports.

Protocols implemented by infrastructure (LangChain, pgvector, etc.).
"""

from collections.abc import AsyncIterator
from typing import Protocol

from app.domain.chat.entities import ChatMessage


# ────────────────────────────────────────────────────────
# LLMPort
# Internal — domain layer
# Contract for language models — infrastructure supplies LangChain/OpenAI/Gemini.
# ────────────────────────────────────────────────────────
class LLMPort(Protocol):
    """Language model — application never imports LangChain / OpenAI / Gemini."""

    # ────────────────────────────────────────────────────────
    # stream
    # Internal — domain layer
    # Yields AI reply tokens one at a time for live streaming.
    # ────────────────────────────────────────────────────────
    def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]: ...

    # ────────────────────────────────────────────────────────
    # complete
    # Internal — domain layer
    # Returns the full AI reply in one call (non-streaming).
    # ────────────────────────────────────────────────────────
    async def complete(self, messages: list[ChatMessage]) -> str: ...

    # ────────────────────────────────────────────────────────
    # summarize
    # Internal — domain layer
    # Shortens a conversation transcript into a brief title or summary.
    # ────────────────────────────────────────────────────────
    async def summarize(self, transcript: str) -> str: ...


# ────────────────────────────────────────────────────────
# RetrieverPort
# Internal — domain layer
# Contract for knowledge search — vector/keyword logic stays in infrastructure.
# ────────────────────────────────────────────────────────
class RetrieverPort(Protocol):
    """Knowledge retrieval — vector / keyword search stays in infrastructure."""

    # ────────────────────────────────────────────────────────
    # retrieve
    # Internal — domain layer
    # Finds relevant knowledge-base text for the user's query, or returns None.
    # ────────────────────────────────────────────────────────
    async def retrieve(self, user_id: str, query: str) -> str | None: ...
