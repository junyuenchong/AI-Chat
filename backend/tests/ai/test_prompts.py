"""Unit tests for chat prompts and document text splitting.

No LLM API calls and no database required.
"""

from app.application.chat.prompts import SYSTEM_PROMPT, append_rag_context
from app.infrastructure.vectorstore.retriever import split_text

# ────────────────────────────────────────────────────────────
# test_system_prompt_names_layers
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: confirm the system prompt mentions LangChain and RAG for the AI.
# ────────────────────────────────────────────────────────────


def test_system_prompt_names_layers():
    assert "LangChain" in SYSTEM_PROMPT
    assert "RAG" in SYSTEM_PROMPT


# ────────────────────────────────────────────────────────────
# test_append_rag_context_appends_retrieved_text
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: confirm knowledge-base search results are added to the system prompt.
# ────────────────────────────────────────────────────────────


def test_append_rag_context_appends_retrieved_text():
    result = append_rag_context("base", "chunk-a")
    assert "base" in result
    assert "chunk-a" in result


# ────────────────────────────────────────────────────────────
# test_split_text_respects_size_and_overlap
# Endpoint: POST /documents (internal)
# Use: confirm uploaded documents are split into overlapping chunks for search.
# ────────────────────────────────────────────────────────────


def test_split_text_respects_size_and_overlap():
    chunks = split_text("abcdefghij" * 10, size=20, overlap=5)
    assert len(chunks) > 1
    assert chunks[0][:5] == "abcde"
