"""Unit tests for knowledge-base search (retriever).

Uses a mocked database — no embeddings API or Postgres required.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.infrastructure.vectorstore.retriever import retrieve_context

# ────────────────────────────────────────────────────────────
# test_retrieve_context_keyword_match
# Endpoint: POST /chat/complete, POST /chat/stream (internal — RAG search)
# Use: keyword search returns matching document chunks as context text.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_context_keyword_match(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.vectorstore.retrieval_strategies.get_embeddings",
        lambda: None,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["annual leave is 14 days"]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    context = await retrieve_context(mock_db, "user-1", "annual leave")
    assert context == "annual leave is 14 days"
    mock_db.execute.assert_awaited()


# ────────────────────────────────────────────────────────────
# test_retrieve_context_returns_none_when_no_chunks
# Endpoint: POST /chat/complete, POST /chat/stream (internal — RAG search)
# Use: when no documents match, return None so chat falls back to direct LLM.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_context_returns_none_when_no_chunks(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.vectorstore.retrieval_strategies.get_embeddings",
        lambda: None,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    context = await retrieve_context(mock_db, "user-1", "anything")
    assert context is None
