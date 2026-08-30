"""Unit tests for Q2 chat chain (history + LLM, no RAG)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.exceptions import LLMError
from app.infrastructure.ai.langchain.chains import ChatChain, build_llm_messages
from app.infrastructure.ai.langchain.llm import LLMProviderError


@pytest.mark.asyncio
async def test_build_llm_messages_includes_system_history_and_user():
    messages = build_llm_messages(
        history=[("user", "hi"), ("assistant", "hello")],
        user_message="what is streaming?",
    )
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "what is streaming?"}
    assert ("user", "hi") in [(m["role"], m["content"]) for m in messages]


@pytest.mark.asyncio
async def test_generate_full_reply_returns_answer():
    llm = AsyncMock()
    llm.complete = AsyncMock(return_value="Hello there")
    chain = ChatChain(llm)

    result = await chain.generate_full_reply("hi", [])
    assert result["answer"] == "Hello there"


@pytest.mark.asyncio
async def test_stream_yields_tokens():
    llm = MagicMock()

    async def fake_stream(messages):
        yield "token-"
        yield "one"

    llm.stream = fake_stream
    chain = ChatChain(llm)

    events = []
    async for name, data in chain.generate_streaming_tokens("hi", []):
        events.append((name, data))

    assert events == [("token", "token-"), ("token", "one")]


@pytest.mark.asyncio
async def test_streaming_maps_llm_provider_error_to_error_event():
    async def failing_stream(_messages):
        raise LLMProviderError("boom", user_message="LLM down")
        yield ""  # pragma: no cover

    llm = MagicMock()
    llm.stream = failing_stream
    chain = ChatChain(llm)

    events = []
    async for name, data in chain.generate_streaming_tokens("hi", []):
        events.append((name, data))

    assert events == [("error", "LLM down")]


@pytest.mark.asyncio
async def test_complete_maps_llm_provider_error_to_domain_error():
    llm = AsyncMock()
    llm.complete = AsyncMock(
        side_effect=LLMProviderError("boom", user_message="LLM down")
    )
    chain = ChatChain(llm)

    with pytest.raises(LLMError, match="LLM down"):
        await chain.generate_full_reply("hi", [])
