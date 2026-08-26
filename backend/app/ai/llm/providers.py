"""LangChain LLM helpers: stream, complete, summarize."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.ai.llm.factory import get_chat_model
from app.ai.prompts.chat import SYSTEM_PROMPT, with_rag_context
from app.ai.prompts.rag import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT


def build_lc_messages(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None = None,
) -> list[BaseMessage]:
    """Build LangChain messages: system (+ RAG) + recent history + user turn."""
    messages: list[BaseMessage] = [SystemMessage(content=with_rag_context(SYSTEM_PROMPT, rag_context))]
    # Keep a short window so prompts stay within model context limits.
    for role, content in history[-12:]:
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_message))
    return messages


def _chunk_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
        return "".join(parts)
    return ""


def demo_reply(user_message: str, rag_context: str | None) -> str:
    """Offline reply when no LLM API key is set."""
    rag_note = (
        f"RAG context used:\n{rag_context[:500]}"
        if rag_context
        else "No RAG hits. Upload a document or ask about LangChain and RAG."
    )
    return (
        "Demo mode is on because GEMINI_API_KEY is empty. "
        "The HTTP path, PostgreSQL persistence, Redis rate limit, and SSE stream "
        "still run for real.\n\n"
        f"You said: {user_message[:300]}\n\n"
        "LangChain = AI components (LLM, prompts, embeddings). "
        "RAG = Retriever + Knowledge chunks + LLM.\n\n"
        f"{rag_note}"
    )


async def stream_reply(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None = None,
) -> AsyncIterator[str]:
    """Yield token strings for SSE (demo word-stream if no API key)."""

    # ---------------------------------------------------------------------------
    # Demo mode — empty API key still exercises SSE end-to-end.
    # ---------------------------------------------------------------------------
    llm = get_chat_model()
    if llm is None:
        text = demo_reply(user_message, rag_context)
        for word in text.split(" "):
            yield word + " "
            await asyncio.sleep(0.02)
        return

    # ---------------------------------------------------------------------------
    # Live LLM stream — never kill SSE on mid-reply failure.
    # ---------------------------------------------------------------------------
    messages = build_lc_messages(history, user_message, rag_context)
    try:
        async for chunk in llm.astream(messages):
            text = _chunk_text(chunk.content)
            if text:
                yield text
    except Exception:
        yield " The language model failed mid-reply. Please try again."


async def complete_reply(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None = None,
) -> str:
    """Collect stream_reply into one string for /chat/complete."""
    parts: list[str] = []
    async for token in stream_reply(history, user_message, rag_context):
        parts.append(token)
    return "".join(parts).strip()


async def summarize_messages(transcript: str) -> str:
    """Short conversation summary for the ARQ summarize job."""
    llm = get_chat_model()
    prompt = SUMMARIZE_USER_PROMPT.format(transcript=transcript[:8000])
    if llm is None:
        compact = " ".join(transcript.split())
        return f"Demo summary: {compact[:280]}"

    try:
        result = await llm.ainvoke(
            [
                SystemMessage(content=SUMMARIZE_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
    except Exception:
        compact = " ".join(transcript.split())
        return f"Summary unavailable. Preview: {compact[:280]}"
    content = result.content
    return content if isinstance(content, str) else str(content)
