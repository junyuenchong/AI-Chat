"""
Token streaming from the LLM port into chat chain events.

Request path:
  infrastructure/ai/langchain/chains/chat_chain.py
    → infrastructure/ai/langchain/callbacks/streaming.py  (this file)
    → infrastructure/ai/langchain/llm/provider.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.domain.chat.entities import ChatMessage
from app.domain.chat.ports import LLMPort
from app.infrastructure.ai.langchain.llm import LLMProviderError


# ────────────────────────────────────────────────────────
# stream_llm_tokens
# Path: infrastructure/ai/langchain/callbacks/streaming.py
# Endpoint: POST /chat/stream (via ChatChain)
# Use: wrap LLMPort.stream and yield (event, payload) tuples for SSE mapping.
# ────────────────────────────────────────────────────────
async def stream_llm_tokens(
    llm: LLMPort,
    messages: list[ChatMessage],
) -> AsyncIterator[tuple[str, str]]:
    """Yield (event_name, payload) tuples for ChatService SSE mapping."""
    try:
        # Step 1 — stream tokens from the LLM port.
        async for token in llm.stream(messages):
            # Step 2 — emit each token as a ("token", text) event.
            yield ("token", token)
    except LLMProviderError as exc:
        # Step 3 — on provider failure, emit an ("error", message) event.
        yield ("error", exc.user_message)
