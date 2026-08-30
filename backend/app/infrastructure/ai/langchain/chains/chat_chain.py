"""
LangChain chat chain — Q2 core.

Build prompt + history → call LLM → stream tokens.
Implements the domain ChatEngine port (not an agent, no RAG).

Request path:
  api/v1/chat/router.py
    → application/chat/service.py
    → domain/chat/ports.py (ChatEngine)
    → infrastructure/ai/langchain/chains/chat_chain.py  (this file)
    → infrastructure/ai/langchain/llm/provider.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.exceptions import LLMError
from app.domain.chat.entities import ChatMessage, ChatResult
from app.domain.chat.ports import LLMPort
from app.infrastructure.ai.langchain.callbacks import stream_llm_tokens
from app.infrastructure.ai.langchain.llm import LLMProviderError
from app.infrastructure.ai.langchain.prompts import SYSTEM_PROMPT
from app.shared.constants import CHAT_HISTORY_LIMIT


# ────────────────────────────────────────────────────────
# build_llm_messages
# Path: infrastructure/ai/langchain/chains/chat_chain.py
# Internal — called by ChatChain before every LLM call.
# Use: assemble system prompt + recent history + current user message.
# ────────────────────────────────────────────────────────
def build_llm_messages(
    history: list[tuple[str, str]],
    user_message: str,
) -> list[ChatMessage]:
    """Build the message list sent to the LLM."""
    # Step 1 — start with the fixed system prompt.
    messages: list[ChatMessage] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Step 2 — append the most recent turns (capped by CHAT_HISTORY_LIMIT).
    for role, content in history[-CHAT_HISTORY_LIMIT:]:
        messages.append({"role": role, "content": content})
    # Step 3 — append the current user message as the final turn.
    messages.append({"role": "user", "content": user_message})
    return messages


class ChatChain:
    """ChatEngine — prompt assembly + LLM stream/complete."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Path: infrastructure/ai/langchain/chains/chat_chain.py
    # Internal — created by adapters/chat_engine.py.
    # Use: store the LLMPort used for complete and stream calls.
    # ────────────────────────────────────────────────────────
    def __init__(self, llm: LLMPort) -> None:
        """Receive the LLM port from dependency injection."""
        self._llm = llm

    # ────────────────────────────────────────────────────────
    # generate_full_reply
    # Path: infrastructure/ai/langchain/chains/chat_chain.py
    # Endpoint: POST /chat/complete
    # Use: build messages, call LLM once, return the full assistant reply.
    # ────────────────────────────────────────────────────────
    async def generate_full_reply(
        self,
        message: str,
        history: list[tuple[str, str]],
    ) -> ChatResult:
        """Generate one full reply from chat history."""
        try:
            # Step 1 — build the LangChain-ready message list.
            messages = build_llm_messages(history, message)
            # Step 2 — call the LLM port (retry + fallback handled in provider).
            answer = await self._llm.complete(messages)
        except LLMProviderError as exc:
            # Step 3 — map infrastructure error to domain LLMError (HTTP 502).
            raise LLMError(exc.user_message) from exc
        # Step 4 — return the answer for ChatService to persist.
        return {"answer": answer}

    # ────────────────────────────────────────────────────────
    # generate_streaming_tokens
    # Path: infrastructure/ai/langchain/chains/chat_chain.py
    # Endpoint: POST /chat/stream
    # Use: build messages, stream tokens, yield (event, payload) tuples for SSE.
    # ────────────────────────────────────────────────────────
    async def generate_streaming_tokens(
        self,
        message: str,
        history: list[tuple[str, str]],
    ) -> AsyncIterator[tuple[str, str]]:
        """Yield token/error events for ChatService SSE framing."""
        # Step 1 — build the LangChain-ready message list.
        messages = build_llm_messages(history, message)
        # Step 2 — delegate streaming to the callback helper.
        async for event in stream_llm_tokens(self._llm, messages):
            yield event
