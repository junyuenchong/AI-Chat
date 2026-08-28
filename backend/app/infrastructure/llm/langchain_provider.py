"""
LangChain LLM provider.

Concrete implementation of LLMPort using LangChain.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.application.chat.prompts import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT
from app.core.config import get_settings
from app.domain.chat.entities import ChatMessage
from app.infrastructure.llm.provider_registry import build_chat_model

logger = logging.getLogger(__name__)

_ROLE_TO_LC: dict[str, Callable[[str], BaseMessage]] = {
    "system": SystemMessage,
    "assistant": AIMessage,
    "user": HumanMessage,
}


# ────────────────────────────────────────────────────────
# _get_chat_model
# Internal — LLM provider
# Builds the configured LangChain chat model, or None in demo mode.
# ────────────────────────────────────────────────────────
def _get_chat_model():
    # Resolve settings and build the configured LangChain chat model.
    return build_chat_model(get_settings())


# ────────────────────────────────────────────────────────
# _to_lc_messages
# Internal — LLM provider
# Converts domain chat messages into LangChain message objects.
# ────────────────────────────────────────────────────────
def _to_lc_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    lc: list[BaseMessage] = []
    for msg in messages:
        # Unpack role and content from each domain message dict.
        role, content = msg["role"], msg["content"]
        # Pick the LangChain message class for this role (default to HumanMessage).
        if role in _ROLE_TO_LC:
            lc.append(_ROLE_TO_LC[role](content))
        else:
            lc.append(HumanMessage(content))
    return lc


# ────────────────────────────────────────────────────────
# _chunk_part
# Internal — LLM provider
# Extracts plain text from one streaming chunk part.
# ────────────────────────────────────────────────────────
def _chunk_part(part: object) -> str:
    # Plain string parts pass through unchanged.
    if isinstance(part, str):
        return part
    # Structured text blocks expose their text field.
    if isinstance(part, dict) and part.get("type") == "text":
        return str(part.get("text", ""))
    # Ignore unrecognized chunk shapes.
    return ""


# ────────────────────────────────────────────────────────
# _chunk_text
# Internal — LLM provider
# Normalizes a streaming chunk into a single text string.
# ────────────────────────────────────────────────────────
def _chunk_text(content: object) -> str:
    # Already a string — return as-is.
    if isinstance(content, str):
        return content
    # Concatenate text from each part in a multi-part chunk.
    if isinstance(content, list):
        return "".join(_chunk_part(part) for part in content)
    return ""


# ────────────────────────────────────────────────────────
# _demo_reply
# Internal — LLM provider
# Returns a canned reply when no API key is configured.
# ────────────────────────────────────────────────────────
def _demo_reply(messages: list[ChatMessage]) -> str:
    # Walk history backwards to find the latest user turn.
    user_message = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    # Pull system prompt text so we can detect injected RAG context.
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    rag_context = system if "Retrieved context:" in system else None
    # Note whether RAG context was present in the system prompt.
    rag_note = (
        f"RAG context used:\n{rag_context[:500]}"
        if rag_context
        else "No RAG hits. Upload a document or ask about LangChain and RAG."
    )
    # Assemble the full demo reply explaining stack behavior and RAG status.
    return (
        "Demo mode is on because GEMINI_API_KEY is empty. "
        "The HTTP path, PostgreSQL persistence, Redis rate limit, and SSE stream "
        "still run for real.\n\n"
        f"You said: {user_message[:300]}\n\n"
        "LangChain = AI components (LLM, prompts, embeddings). "
        "RAG = Retriever + Knowledge chunks + LLM.\n\n"
        f"{rag_note}"
    )


# ────────────────────────────────────────────────────────
# _demo_summary
# Internal — LLM provider
# Returns a truncated preview summary when the LLM is unavailable.
# ────────────────────────────────────────────────────────
def _demo_summary(transcript: str, *, prefix: str) -> str:
    # Collapse whitespace so the preview fits on one line.
    compact = " ".join(transcript.split())
    return f"{prefix}: {compact[:280]}"


def _user_facing_llm_error(exc: Exception) -> str:
    """Map provider exceptions to a short, actionable chat message."""
    message = str(exc).lower()
    if "permission_denied" in message or "denied access" in message:
        return (
            " Gemini API access is denied for this Google Cloud project. "
            "Enable billing and the Gemini API on the project linked to your key, "
            "or use demo mode (empty GEMINI_API_KEY)."
        )
    if "quota" in message or "429" in message:
        return (
            " Gemini API quota exceeded for this project. "
            "Check billing and rate limits in Google AI Studio, then try again."
        )
    if "not_found" in message or "no longer available" in message:
        return (
            " The configured Gemini model is unavailable. "
            "Set GEMINI_MODEL=gemini-3.6-flash in .env and restart the API."
        )
    return " The language model failed mid-reply. Please try again."


class LangChainProvider:
    """LLMPort backed by LangChain (Gemini / OpenAI / demo)."""

    # ────────────────────────────────────────────────────────
    # stream
    # Internal — LLM provider
    # Streams assistant tokens from the configured model or demo fallback.
    # ────────────────────────────────────────────────────────
    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        llm = _get_chat_model()
        if llm is None:
            # Demo mode — stream words with a short delay to simulate tokens.
            text = _demo_reply(messages)
            for word in text.split(" "):
                yield word + " "
                await asyncio.sleep(0.02)
            return

        # Convert domain messages before calling the LangChain model.
        lc_messages = _to_lc_messages(messages)
        try:
            async for chunk in llm.astream(lc_messages):
                # Normalize each chunk to plain text before yielding.
                text = _chunk_text(chunk.content)
                if text:
                    yield text
        except Exception as exc:
            logger.exception("Gemini/LLM stream failed")
            yield _user_facing_llm_error(exc)

    # ────────────────────────────────────────────────────────
    # complete
    # Internal — LLM provider
    # Collects the full assistant reply from the streaming path.
    # ────────────────────────────────────────────────────────
    async def complete(self, messages: list[ChatMessage]) -> str:
        parts: list[str] = []
        # Drain the stream and accumulate every token.
        async for token in self.stream(messages):
            parts.append(token)
        return "".join(parts).strip()

    # ────────────────────────────────────────────────────────
    # summarize
    # Internal — LLM provider
    # Produces a short summary of a conversation transcript.
    # ────────────────────────────────────────────────────────
    async def summarize(self, transcript: str) -> str:
        llm = _get_chat_model()
        if llm is None:
            # No API key — return a truncated preview instead of calling the LLM.
            return _demo_summary(transcript, prefix="Demo summary")

        # Cap transcript length to stay within model context limits.
        prompt = SUMMARIZE_USER_PROMPT.format(transcript=transcript[:8000])
        try:
            result = await llm.ainvoke(
                [
                    SystemMessage(content=SUMMARIZE_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
            )
        except Exception:
            return _demo_summary(transcript, prefix="Summary unavailable. Preview")
        content = result.content
        return content if isinstance(content, str) else str(content)


_default_provider = LangChainProvider()


# ────────────────────────────────────────────────────────
# stream_reply
# Internal — LLM provider
# Builds prompt history and streams a chat reply for the application layer.
# ────────────────────────────────────────────────────────
async def stream_reply(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None = None,
) -> AsyncIterator[str]:
    from app.application.chat.prompts import SYSTEM_PROMPT, append_rag_context

    # System prompt (+ optional RAG), recent history, then the user turn.
    messages: list[ChatMessage] = [
        {"role": "system", "content": append_rag_context(SYSTEM_PROMPT, rag_context)},
        *[{"role": role, "content": content} for role, content in history[-12:]],
        {"role": "user", "content": user_message},
    ]
    async for token in _default_provider.stream(messages):
        yield token


# ────────────────────────────────────────────────────────
# complete_reply
# Internal — LLM provider
# Returns the full assistant reply by draining the stream.
# ────────────────────────────────────────────────────────
async def complete_reply(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None = None,
) -> str:
    parts: list[str] = []
    # Drain the streaming reply and join into one string.
    async for token in stream_reply(history, user_message, rag_context):
        parts.append(token)
    return "".join(parts).strip()


# ────────────────────────────────────────────────────────
# summarize_messages
# Internal — LLM provider
# Summarizes a transcript via the shared default provider.
# ────────────────────────────────────────────────────────
async def summarize_messages(transcript: str) -> str:
    # Delegate to the module-level default LangChain provider.
    return await _default_provider.summarize(transcript)


# ────────────────────────────────────────────────────────
# build_lc_messages
# Internal — LLM provider
# Builds LangChain messages from history, user input, and optional RAG context.
# ────────────────────────────────────────────────────────
def build_lc_messages(
    history: list[tuple[str, str]],
    user_message: str,
    rag_context: str | None = None,
) -> list[BaseMessage]:
    from app.application.chat.prompts import SYSTEM_PROMPT, append_rag_context

    # Convert the assembled domain messages into LangChain message objects.
    return _to_lc_messages(
        [
            {
                "role": "system",
                "content": append_rag_context(SYSTEM_PROMPT, rag_context),
            },
            *[{"role": role, "content": content} for role, content in history[-12:]],
            {"role": "user", "content": user_message},
        ]
    )


# ────────────────────────────────────────────────────────
# demo_reply
# Internal — LLM provider
# Exposes the demo-mode reply helper for tests and diagnostics.
# ────────────────────────────────────────────────────────
def demo_reply(user_message: str, rag_context: str | None) -> str:
    from app.application.chat.prompts import SYSTEM_PROMPT, append_rag_context

    # Build a minimal two-turn prompt and run the demo reply path.
    return _demo_reply(
        [
            {
                "role": "system",
                "content": append_rag_context(SYSTEM_PROMPT, rag_context),
            },
            {"role": "user", "content": user_message},
        ]
    )
