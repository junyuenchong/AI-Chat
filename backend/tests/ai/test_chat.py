"""Unit tests for chat helpers (RAG routing and streaming).

Uses mocked LLM and retriever ports — no API keys or database.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.application.chat.helpers import (
    fetch_rag_context,
    generate_full_reply,
    generate_streaming_tokens,
    should_refuse_without_rag_context,
)
from app.core.config import get_settings
from app.core.exceptions import LLMError
from app.infrastructure.llm.errors import LLMProviderError


def _ports(*, retriever=None, llm=None):
    return llm or MagicMock(), retriever or MagicMock()


# ────────────────────────────────────────────────────────────
# test_optional_rag_skips_when_disabled
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: when use_rag=false, skip knowledge search and use direct LLM route.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_optional_rag_skips_when_disabled():
    llm, retriever = _ports()
    route, context = await fetch_rag_context(retriever, "u", "hello", use_rag=False)
    assert route == "direct"
    assert context is None


# ────────────────────────────────────────────────────────────
# test_optional_rag_uses_rag_route_when_context_found
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: when documents match the question, route should be "rag".
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_optional_rag_uses_rag_route_when_context_found():
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value="policy chunk text")
    llm, _ = _ports(retriever=retriever)
    route, context = await fetch_rag_context(
        retriever, "user-1", "annual leave", use_rag=True
    )
    assert route == "rag"
    assert context == "policy chunk text"


# ────────────────────────────────────────────────────────────
# test_optional_rag_falls_back_to_direct_when_no_chunks
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: when search finds nothing, fall back to direct LLM without error.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_optional_rag_falls_back_to_direct_when_no_chunks():
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value=None)
    llm, _ = _ports(retriever=retriever)
    route, context = await fetch_rag_context(
        retriever, "user-1", "anything", use_rag=True
    )
    assert route == "direct"
    assert context is None


# ────────────────────────────────────────────────────────────
# test_optional_rag_fail_soft_on_retriever_error
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: when search fails, chat still works via direct LLM route.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_optional_rag_fail_soft_on_retriever_error():
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(side_effect=RuntimeError("db down"))
    llm, _ = _ports(retriever=retriever)
    route, context = await fetch_rag_context(retriever, "user-1", "query", use_rag=True)
    assert route == "direct"
    assert context is None


# ────────────────────────────────────────────────────────────
# test_generate_full_reply_returns_answer_and_route
# Endpoint: POST /chat/complete (internal)
# Use: non-streaming path returns the LLM answer and route name.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_full_reply_returns_answer_and_route():
    llm = AsyncMock()
    llm.complete = AsyncMock(return_value="Hello there")
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value=None)

    result = await generate_full_reply(llm, retriever, "u", "hi", [], use_rag=False)
    assert result["route"] == "direct"
    assert result["answer"] == "Hello there"


# ────────────────────────────────────────────────────────────
# test_stream_chat_yields_route_rag_then_tokens
# Endpoint: POST /chat/stream (internal)
# Use: streaming path sends route, rag flag, then token events in order.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_chat_yields_route_rag_then_tokens():
    llm = MagicMock()
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value="ctx")

    async def fake_stream(messages):
        yield "token-"
        yield "one"

    llm.stream = fake_stream

    events = []
    async for name, data in generate_streaming_tokens(
        llm, retriever, "u", "hi", [], use_rag=True
    ):
        events.append((name, data))

    assert events[0] == ("route", "rag")
    assert events[1] == ("rag", "1")
    assert ("token", "token-") in events
    assert ("token", "one") in events


@pytest.fixture
def strict_rag_mode(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RAG_STRICT_MODE", "true")
    yield
    get_settings.cache_clear()


@pytest.fixture
def hybrid_rag_mode(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RAG_STRICT_MODE", "false")
    yield
    get_settings.cache_clear()


# ────────────────────────────────────────────────────────────
# test_should_refuse_without_rag_context_when_strict
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: strict mode refuses when RAG is on but retrieval returned nothing.
# ────────────────────────────────────────────────────────────


def test_should_refuse_without_rag_context_when_strict(strict_rag_mode):
    assert should_refuse_without_rag_context(True, None) is True
    assert should_refuse_without_rag_context(True, "chunk") is False
    assert should_refuse_without_rag_context(False, None) is False


def test_should_not_refuse_in_hybrid_mode(hybrid_rag_mode):
    assert should_refuse_without_rag_context(True, None) is False


# ────────────────────────────────────────────────────────────
# test_strict_rag_refuses_without_calling_llm
# Endpoint: POST /chat/complete (internal)
# Use: strict mode returns a fixed message and does not call the LLM.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_strict_rag_refuses_without_calling_llm(strict_rag_mode):
    llm = AsyncMock()
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value=None)

    result = await generate_full_reply(llm, retriever, "u", "Python?", [], use_rag=True)

    assert result["route"] == "rag"
    assert "knowledge base" in result["answer"].lower()
    llm.complete.assert_not_called()


# ────────────────────────────────────────────────────────────
# test_strict_rag_stream_refuses_without_calling_llm
# Endpoint: POST /chat/stream (internal)
# Use: strict mode streams the refusal message without LLM tokens.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_strict_rag_stream_refuses_without_calling_llm(strict_rag_mode):
    llm = AsyncMock()
    llm.stream = AsyncMock()
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value=None)

    events = []
    async for name, data in generate_streaming_tokens(
        llm, retriever, "u", "Python?", [], use_rag=True
    ):
        events.append((name, data))

    assert events[0] == ("route", "direct")
    assert events[1] == ("rag", "0")
    assert len(events) == 3
    assert events[2][0] == "token"
    assert "knowledge base" in events[2][1].lower()
    llm.stream.assert_not_called()


@pytest.mark.asyncio
async def test_streaming_maps_llm_provider_error_to_error_event():
    async def failing_stream(_messages):
        raise LLMProviderError("boom", user_message="LLM down")
        yield ""  # pragma: no cover

    llm = MagicMock()
    llm.stream = failing_stream
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value=None)

    events = []
    async for name, data in generate_streaming_tokens(
        llm, retriever, "u", "hi", [], use_rag=False
    ):
        events.append((name, data))

    assert ("error", "LLM down") in events
    assert not any(name == "token" for name, _ in events)


@pytest.mark.asyncio
async def test_complete_maps_llm_provider_error_to_domain_error(hybrid_rag_mode):
    llm = AsyncMock()
    llm.complete = AsyncMock(
        side_effect=LLMProviderError("boom", user_message="LLM down")
    )
    retriever = AsyncMock()
    retriever.retrieve = AsyncMock(return_value=None)

    with pytest.raises(LLMError, match="LLM down"):
        await generate_full_reply(llm, retriever, "u", "hi", [], use_rag=True)
