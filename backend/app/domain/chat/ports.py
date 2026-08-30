"""
Chat domain ports.

Protocols implemented by infrastructure (LangChain adapters).
"""

from collections.abc import AsyncIterator
from typing import Protocol

from app.domain.chat.entities import ChatMessage, ChatResult


class LLMPort(Protocol):
    """Language model — application never imports LangChain / OpenAI / Gemini."""

    def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]: ...

    async def complete(self, messages: list[ChatMessage]) -> str: ...


class ChatEngine(Protocol):
    """Chat orchestration — history + prompt + LLM stream/complete."""

    async def generate_full_reply(
        self,
        message: str,
        history: list[tuple[str, str]],
    ) -> ChatResult: ...

    async def generate_streaming_tokens(
        self,
        message: str,
        history: list[tuple[str, str]],
    ) -> AsyncIterator[tuple[str, str]]: ...
