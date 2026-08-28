"""LangChain LLM adapter — streams and completes via configured model chain."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.application.chat.prompts import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT
from app.domain.chat.entities import ChatMessage
from app.infrastructure.llm.errors import LLMProviderError
from app.infrastructure.llm.langchain.chunk_parser import chunk_text
from app.infrastructure.llm.langchain.message_mapper import to_lc_messages

logger = logging.getLogger(__name__)


class LangChainProvider:
    """Adapter: domain messages in, LangChain model chain out. No prompt orchestration."""

    def __init__(self, model_chain: list[tuple[str, Any]]) -> None:
        if not model_chain:
            raise ValueError("LangChainProvider requires at least one model.")
        self._model_chain = model_chain

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        lc_messages = to_lc_messages(messages)
        last_exc: Exception | None = None
        for label, llm in self._model_chain:
            try:
                async for chunk in llm.astream(lc_messages):
                    text = chunk_text(chunk.content)
                    if text:
                        yield text
                return
            except Exception as exc:
                logger.warning("LLM stream failed for %s", label, exc_info=exc)
                last_exc = exc
        raise LLMProviderError.from_exception(last_exc)

    async def complete(self, messages: list[ChatMessage]) -> str:
        lc_messages = to_lc_messages(messages)
        last_exc: Exception | None = None
        for label, llm in self._model_chain:
            try:
                result = await llm.ainvoke(lc_messages)
                content = result.content
                return content if isinstance(content, str) else str(content)
            except Exception as exc:
                logger.warning("LLM complete failed for %s", label, exc_info=exc)
                last_exc = exc
        raise LLMProviderError.from_exception(last_exc)

    async def summarize(self, transcript: str) -> str:
        prompt = SUMMARIZE_USER_PROMPT.format(transcript=transcript[:8000])
        summarize_messages: list[ChatMessage] = [
            {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return await self.complete(summarize_messages)
