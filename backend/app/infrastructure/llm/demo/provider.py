"""Demo LLM provider — canned replies when no API key is configured."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.application.chat.prompts import SYSTEM_PROMPT, append_rag_context
from app.domain.chat.entities import ChatMessage


def demo_reply_text(user_message: str, rag_context: str | None) -> str:
    """Build a demo reply for tests and offline mode."""
    messages: list[ChatMessage] = [
        {
            "role": "system",
            "content": append_rag_context(SYSTEM_PROMPT, rag_context),
        },
        {"role": "user", "content": user_message},
    ]
    return _demo_reply(messages)


def _demo_reply(messages: list[ChatMessage]) -> str:
    user_message = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    rag_context = system if "Retrieved context:" in system else None
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


def _demo_summary(transcript: str, *, prefix: str) -> str:
    compact = " ".join(transcript.split())
    return f"{prefix}: {compact[:280]}"


class DemoProvider:
    """LLMPort for offline/demo deployments — no external API calls."""

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        text = _demo_reply(messages)
        for word in text.split(" "):
            yield word + " "
            await asyncio.sleep(0.02)

    async def complete(self, messages: list[ChatMessage]) -> str:
        return _demo_reply(messages).strip()

    async def summarize(self, transcript: str) -> str:
        return _demo_summary(transcript, prefix="Demo summary")
