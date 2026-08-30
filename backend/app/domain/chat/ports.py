"""
Chat domain ports.

Protocols implemented by infrastructure (LangChain, pgvector, etc.).
"""

from collections.abc import AsyncIterator
from typing import Protocol

from app.domain.chat.entities import ChatMessage, ChatResult


# ────────────────────────────────────────────────────────
# LLMPort
# Internal — domain layer
# Contract for language models — infrastructure supplies LangChain/OpenAI/Gemini.
# ────────────────────────────────────────────────────────
class LLMPort(Protocol):
    """Language model — application never imports LangChain / OpenAI / Gemini."""

    def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]: ...

    async def complete(self, messages: list[ChatMessage]) -> str: ...

    async def summarize(self, transcript: str) -> str: ...


# ────────────────────────────────────────────────────────
# RetrieverPort
# Internal — domain layer
# Contract for knowledge search — vector/keyword logic stays in infrastructure.
# ────────────────────────────────────────────────────────
class RetrieverPort(Protocol):
    """Knowledge retrieval — vector / keyword search stays in infrastructure."""

    async def retrieve(self, user_id: str, query: str) -> str | None: ...


# ────────────────────────────────────────────────────────
# ChatEngine
# Internal — domain layer
# Chat orchestration — RAG routing + LLM stream/complete.
# ────────────────────────────────────────────────────────
class ChatEngine(Protocol):
    """Chat orchestration — RAG routing + LLM stream/complete."""

    async def generate_full_reply(
        self,
        user_id: str,
        message: str,
        history: list[tuple[str, str]],
        use_rag: bool,
    ) -> ChatResult: ...

    def generate_streaming_tokens(
        self,
        user_id: str,
        message: str,
        history: list[tuple[str, str]],
        use_rag: bool,
    ) -> AsyncIterator[tuple[str, str]]: ...
