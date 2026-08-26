"""Chat AI flow unit tests — no LLM, no Postgres.

Covers the RAG on/off branch inside ai/chat.py.
"""

import asyncio

from app.ai.chat import _optional_rag


# ---------------------------------------------------------------------------
# use_rag=False must skip Retriever entirely (direct LLM path).
# ---------------------------------------------------------------------------

def test_optional_rag_skips_when_disabled():
    # db=None is fine here — retrieve_context is never called when use_rag is False.
    route, context = asyncio.run(
        _optional_rag(db=None, user_id="u", message="hello", use_rag=False)  # type: ignore[arg-type]
    )
    assert route == "direct"
    assert context is None
