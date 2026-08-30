"""
LangChain agent.

Orchestrates LLM + RAG + prompts on each chat message.
Called by ChatService — never imported from the API layer.

Flow per message:
  1. Decide route (RAG on or off)
  2. Retrieve document context (retrieval.py)
  3. Build messages (prompts.py)
  4. Call LLM (llm.py)
  5. Return answer or stream tokens
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.core.exceptions import LLMError
from app.domain.chat.entities import ChatMessage, ChatResult
from app.domain.chat.ports import LLMPort, RetrieverPort
from app.infrastructure.ai.langchain.llm import LLMProviderError, build_llm_port
from app.infrastructure.ai.langchain.prompts import (
    STRICT_RAG_EMPTY_REPLY,
    SYSTEM_PROMPT,
    append_rag_context,
)
from app.shared.constants import CHAT_HISTORY_LIMIT


# ────────────────────────────────────────────────────────
# build_llm_messages
# Internal — langchain / agent
# Assembles system prompt, history, and user message for the LLM.
# ────────────────────────────────────────────────────────
def build_llm_messages(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None,
) -> list[ChatMessage]:
    """Build the message list sent to the LLM."""
    # Step 1: system prompt with optional RAG context appended.
    messages: list[ChatMessage] = [
        {"role": "system", "content": append_rag_context(SYSTEM_PROMPT, rag_context)},
    ]
    # Step 2: last N turns from chat history.
    for role, content in history[-CHAT_HISTORY_LIMIT:]:
        messages.append({"role": role, "content": content})
    # Step 3: current user message.
    messages.append({"role": "user", "content": user_message})
    return messages


# ────────────────────────────────────────────────────────
# fetch_rag_context
# Internal — langchain / agent
# Decides whether to use RAG and fetches document context.
# ────────────────────────────────────────────────────────
async def fetch_rag_context(
    retriever: RetrieverPort,
    user_id: str,
    message: str,
    use_rag: bool,
) -> tuple[str, str | None]:
    """Return (route, context) — route is 'direct' or 'rag'."""
    # RAG disabled — skip retrieval and use the LLM directly.
    if not use_rag:
        return "direct", None
    try:
        # Search uploaded documents for relevant chunks.
        context = await retriever.retrieve(user_id, message)
    except Exception:
        context = None
    # Mark route as 'rag' only when context was actually found.
    return ("rag" if context else "direct"), context


# ────────────────────────────────────────────────────────
# should_refuse_without_rag_context
# Internal — langchain / agent
# Refuses to answer when strict mode is on but no documents matched.
# ────────────────────────────────────────────────────────
def should_refuse_without_rag_context(use_rag: bool, rag_context: str | None) -> bool:
    """Return True when RAG is required but retrieval returned nothing."""
    if not use_rag or rag_context:
        return False
    return get_settings().rag_strict_mode


class ChatAgent:
    """ChatEngine — routes between direct LLM and RAG, then streams or completes."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — langchain / agent
    # Stores LLM and retriever ports injected by build_chat_engine().
    # ────────────────────────────────────────────────────────
    def __init__(self, llm: LLMPort, retriever: RetrieverPort) -> None:
        self._llm = llm
        self._retriever = retriever

    # ────────────────────────────────────────────────────────
    # generate_full_reply
    # Endpoint: POST /chat/complete (internal)
    # Returns the full AI reply in one call (non-streaming).
    # ────────────────────────────────────────────────────────
    async def generate_full_reply(
        self,
        user_id: str,
        message: str,
        history: list[tuple[str, str]],
        use_rag: bool,
    ) -> ChatResult:
        """Generate one full reply with optional RAG."""
        # Step 1: fetch RAG context when enabled.
        route, rag_context = await fetch_rag_context(
            self._retriever, user_id, message, use_rag
        )
        # Step 2: refuse early in strict mode when no documents matched.
        if should_refuse_without_rag_context(use_rag, rag_context):
            return {
                "route": "rag",
                "rag_context": None,
                "answer": STRICT_RAG_EMPTY_REPLY,
            }
        try:
            # Step 3: build messages and call the LLM once.
            messages = build_llm_messages(history, message, rag_context)
            answer = await self._llm.complete(messages)
        except LLMProviderError as exc:
            raise LLMError(exc.user_message) from exc
        # Step 4: return answer with route metadata.
        return {"route": route, "rag_context": rag_context, "answer": answer}

    # ────────────────────────────────────────────────────────
    # generate_streaming_tokens
    # Endpoint: POST /chat/stream (internal)
    # Yields route, RAG, token, and error events for SSE framing.
    # ────────────────────────────────────────────────────────
    async def generate_streaming_tokens(
        self,
        user_id: str,
        message: str,
        history: list[tuple[str, str]],
        use_rag: bool,
    ) -> AsyncIterator[tuple[str, str]]:
        """Yield internal events converted to SSE frames by ChatService."""
        try:
            # Step 1: fetch RAG context when enabled.
            route, rag_context = await fetch_rag_context(
                self._retriever, user_id, message, use_rag
            )
        except Exception:
            yield ("error", "The chat AI flow failed. Please try again.")
            return

        # Step 2: tell the client which route and whether RAG found context.
        yield ("route", route)
        yield ("rag", "1" if rag_context else "0")
        if should_refuse_without_rag_context(use_rag, rag_context):
            yield ("token", STRICT_RAG_EMPTY_REPLY)
            return

        # Step 3: stream tokens from the LLM one at a time.
        messages = build_llm_messages(history, message, rag_context)
        try:
            async for token in self._llm.stream(messages):
                yield ("token", token)
        except LLMProviderError as exc:
            yield ("error", exc.user_message)


# ────────────────────────────────────────────────────────
# generate_full_reply
# Internal — tests only
# Runs ChatAgent without FastAPI dependency injection.
# ────────────────────────────────────────────────────────
async def generate_full_reply(
    llm: LLMPort,
    retriever: RetrieverPort,
    user_id: str,
    message: str,
    history: list[tuple[str, str]],
    use_rag: bool,
) -> ChatResult:
    """Test helper — run the agent without DI."""
    agent = ChatAgent(llm, retriever)
    return await agent.generate_full_reply(user_id, message, history, use_rag)


# ────────────────────────────────────────────────────────
# generate_streaming_tokens
# Internal — tests only
# Streams agent events without FastAPI dependency injection.
# ────────────────────────────────────────────────────────
async def generate_streaming_tokens(
    llm: LLMPort,
    retriever: RetrieverPort,
    user_id: str,
    message: str,
    history: list[tuple[str, str]],
    use_rag: bool,
) -> AsyncIterator[tuple[str, str]]:
    """Test helper — stream events without DI."""
    agent = ChatAgent(llm, retriever)
    async for event in agent.generate_streaming_tokens(
        user_id, message, history, use_rag
    ):
        yield event


# ────────────────────────────────────────────────────────
# summarize_transcript
# Internal — ARQ background job
# Shortens a conversation transcript for the sidebar title.
# ────────────────────────────────────────────────────────
async def summarize_transcript(transcript: str) -> str:
    """Summarize a conversation transcript (background job)."""
    # Build LLM from settings and run the summarize prompt.
    return await build_llm_port().summarize(transcript)
