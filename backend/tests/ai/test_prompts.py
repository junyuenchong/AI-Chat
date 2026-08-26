"""Prompt and chunker tests — no LLM, no Postgres.

Keeps product copy (SYSTEM_PROMPT) and RAG split_text from drifting.
"""

from app.ai.prompts.chat import SYSTEM_PROMPT, with_rag_context
from app.ai.rag.service import split_text


# ---------------------------------------------------------------------------
# System prompt — interview / demo copy must name the AI layers.
# ---------------------------------------------------------------------------

def test_system_prompt_names_layers():
    assert "LangChain" in SYSTEM_PROMPT
    assert "RAG" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# RAG context — retrieved chunks are appended to the system message.
# ---------------------------------------------------------------------------

def test_with_rag_context_appends_retrieved_text():
    result = with_rag_context("base", "chunk-a")
    assert "base" in result
    assert "chunk-a" in result


# ---------------------------------------------------------------------------
# Chunker — overlapping windows used by Knowledge ingest + embed jobs.
# ---------------------------------------------------------------------------

def test_split_text_respects_size_and_overlap():
    chunks = split_text("abcdefghij" * 10, size=20, overlap=5)
    assert len(chunks) > 1
    assert chunks[0][:5] == "abcde"
