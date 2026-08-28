"""
Chat application helpers.

Builds LLM prompts, fetches RAG context, and generates AI replies.
"""

from collections.abc import AsyncIterator

from app.application.chat.prompts import (
    STRICT_RAG_EMPTY_REPLY,
    SYSTEM_PROMPT,
    append_rag_context,
)
from app.core.config import get_settings
from app.core.exceptions import LLMError
from app.domain.chat.entities import ChatMessage, ChatResult
from app.domain.chat.ports import LLMPort, RetrieverPort
from app.infrastructure.llm.errors import LLMProviderError

EMPTY_REPLY = "I could not generate a reply. Please try again."
LLM_FAILURE = "The language model failed. Please try again."


# ────────────────────────────────────────────────────────
# build_llm_messages
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Builds the message list sent to the AI (system prompt + history + user message).
# ────────────────────────────────────────────────────────
def build_llm_messages(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None,
) -> list[ChatMessage]:
    """Assemble system prompt, past messages, and the new user message for the LLM."""
    # Start with the system prompt, optionally enriched with RAG context.
    messages: list[ChatMessage] = [
        {"role": "system", "content": append_rag_context(SYSTEM_PROMPT, rag_context)},
    ]
    # Only last 12 messages — keeps cost and latency down.
    for role, content in history[-12:]:
        messages.append({"role": role, "content": content})
    # Append the current user message last so the model answers it.
    messages.append({"role": "user", "content": user_message})
    return messages


# ────────────────────────────────────────────────────────
# fetch_rag_context
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Searches the knowledge base for relevant text, or skips if RAG is off.
# ────────────────────────────────────────────────────────
async def fetch_rag_context(
    retriever: RetrieverPort,
    user_id: str,
    message: str,
    use_rag: bool,
) -> tuple[str, str | None]:
    """Return route ('direct' or 'rag') and optional retrieved knowledge text."""
    # Skip knowledge search when the client disabled RAG.
    if not use_rag:
        return "direct", None
    try:
        # Search the user's uploaded documents for relevant chunks.
        context = await retriever.retrieve(user_id, message)
    except Exception:
        context = None  # If search fails, answer without knowledge base context.
    # Use the RAG route only when retrieval returned text.
    return ("rag" if context else "direct"), context


# ────────────────────────────────────────────────────────
# should_refuse_without_rag_context
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Returns true when strict RAG is on but retrieval found no usable context.
# ────────────────────────────────────────────────────────
def should_refuse_without_rag_context(use_rag: bool, rag_context: str | None) -> bool:
    """Strict RAG: skip the LLM when knowledge search returned nothing."""
    if not use_rag or rag_context:
        return False
    return get_settings().rag_strict_mode


# ────────────────────────────────────────────────────────
# generate_full_reply
# Endpoint: POST /chat/complete (internal)
# Gets RAG context (if enabled), calls the LLM once, returns the full reply.
# ────────────────────────────────────────────────────────
async def generate_full_reply(
    llm: LLMPort,
    retriever: RetrieverPort,
    user_id: str,
    message: str,
    history: list[tuple[str, str]],
    use_rag: bool,
) -> ChatResult:
    """Generate one complete AI reply for the non-streaming chat endpoint."""
    # Decide whether to use RAG and fetch context if needed.
    route, rag_context = await fetch_rag_context(retriever, user_id, message, use_rag)
    if should_refuse_without_rag_context(use_rag, rag_context):
        return {
            "route": "rag",
            "rag_context": None,
            "answer": STRICT_RAG_EMPTY_REPLY,
        }
    try:
        messages = build_llm_messages(history, message, rag_context)
        answer = await llm.complete(messages)
    except LLMProviderError as exc:
        raise LLMError(exc.user_message) from exc
    return {"route": route, "rag_context": rag_context, "answer": answer}


# ────────────────────────────────────────────────────────
# generate_streaming_tokens
# Endpoint: POST /chat/stream (internal)
# Yields route info first, then AI tokens one at a time for live streaming.
# ────────────────────────────────────────────────────────
async def generate_streaming_tokens(
    llm: LLMPort,
    retriever: RetrieverPort,
    user_id: str,
    message: str,
    history: list[tuple[str, str]],
    use_rag: bool,
) -> AsyncIterator[tuple[str, str]]:
    """Yield internal events: route, rag flag, then each token from the LLM."""
    try:
        # Resolve route and optional RAG context before streaming tokens.
        route, rag_context = await fetch_rag_context(
            retriever, user_id, message, use_rag
        )
    except Exception:
        # Stop the stream early if setup fails.
        yield ("error", "The chat AI flow failed. Please try again.")
        return

    # Tell the client which path and whether RAG was used.
    yield ("route", route)
    yield ("rag", "1" if rag_context else "0")
    if should_refuse_without_rag_context(use_rag, rag_context):
        yield ("token", STRICT_RAG_EMPTY_REPLY)
        return
    messages = build_llm_messages(history, message, rag_context)
    try:
        async for token in llm.stream(messages):
            yield ("token", token)
    except LLMProviderError as exc:
        yield ("error", exc.user_message)
