"""Unit tests for LangChainLLM retry + fallback behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.ai.langchain.llm import LangChainLLM


@pytest.mark.asyncio
async def test_complete_retries_transient_error_before_success():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        side_effect=[Exception("HTTP 503 unavailable"), MagicMock(content="hello")]
    )
    model = LangChainLLM([("gemini", llm)])

    with patch("app.infrastructure.ai.langchain.llm.asyncio.sleep", new_callable=AsyncMock):
        result = await model.complete([{"role": "user", "content": "hi"}])

    assert result == "hello"
    assert llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_complete_fails_over_to_next_model_after_retries():
    primary = MagicMock()
    primary.ainvoke = AsyncMock(side_effect=Exception("HTTP 503 unavailable"))
    fallback = MagicMock()
    fallback.ainvoke = AsyncMock(return_value=MagicMock(content="from fallback"))

    model = LangChainLLM([("primary", primary), ("fallback", fallback)])

    with patch("app.infrastructure.ai.langchain.llm.asyncio.sleep", new_callable=AsyncMock):
        result = await model.complete([{"role": "user", "content": "hi"}])

    assert result == "from fallback"
    assert primary.ainvoke.await_count == 3
    assert fallback.ainvoke.await_count == 1
