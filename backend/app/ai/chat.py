"""Chat AI flow: optional RAG retrieve, then LLM stream or complete."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.providers import complete_reply, stream_reply
from app.ai.rag.retrieve import retrieve_context


class ChatResult(TypedDict, total=False):
    """Result of a non-streaming chat turn."""

    route: str
    rag_context: str | None
    answer: str


async def _optional_rag(
    db: AsyncSession,
    user_id: str,
    message: str,
    use_rag: bool,
) -> tuple[str, str | None]:
    """Return (route, rag_context). route is 'rag' or 'direct'."""

    # ---------------------------------------------------------------------------
    # Client can disable RAG — skip Retriever entirely.
    # ---------------------------------------------------------------------------
    if not use_rag:
        return "direct", None
    try:
        context = await retrieve_context(db, user_id, message)
    except Exception:
        # Fail soft so chat still answers without Knowledge hits.
        context = None
    return ("rag" if context else "direct"), context


async def run_chat(
    db: AsyncSession,
    user_id: str,
    message: str,
    history: list[tuple[str, str]],
    use_rag: bool,
) -> ChatResult:
    """Retrieve (optional) then one LLM reply — used by POST /chat/complete."""

    # ---------------------------------------------------------------------------
    # Optional Knowledge retrieve → one LLM completion.
    # ---------------------------------------------------------------------------
    route, rag_context = await _optional_rag(db, user_id, message, use_rag)
    try:
        answer = await complete_reply(history, message, rag_context)
    except Exception:
        answer = "The language model failed. Please try again."
    return {"route": route, "rag_context": rag_context, "answer": answer}


async def stream_chat(
    db: AsyncSession,
    user_id: str,
    message: str,
    history: list[tuple[str, str]],
    use_rag: bool,
) -> AsyncIterator[tuple[str, str]]:
    """Yield (route|rag|token|error, data) for SSE — used by POST /chat/stream."""

    # ---------------------------------------------------------------------------
    # Meta first (route/rag), then token stream for EventSourceResponse.
    # ---------------------------------------------------------------------------
    try:
        route, rag_context = await _optional_rag(db, user_id, message, use_rag)
    except Exception:
        yield ("error", "The chat AI flow failed. Please try again.")
        return

    yield ("route", route)
    yield ("rag", "1" if rag_context else "0")
    async for token in stream_reply(history, message, rag_context):
        yield ("token", token)
