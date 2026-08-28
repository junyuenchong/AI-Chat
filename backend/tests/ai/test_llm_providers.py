"""Unit tests for LangChain message building and demo LLM replies.

No API keys and no database required.
"""

from app.infrastructure.llm.langchain_provider import build_lc_messages, demo_reply

# ────────────────────────────────────────────────────────────
# test_build_lc_messages_includes_system_and_user
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: confirm messages include system prompt, RAG context, and user turn.
# ────────────────────────────────────────────────────────────


def test_build_lc_messages_includes_system_and_user():
    messages = build_lc_messages(
        history=[("user", "hi"), ("assistant", "hello")],
        user_message="what is RAG?",
        rag_context="chunk about leave policy",
    )
    roles = [m.type for m in messages]
    assert roles[0] == "system"
    assert "chunk about leave policy" in messages[0].content
    assert roles[-1] == "human"
    assert messages[-1].content == "what is RAG?"


# ────────────────────────────────────────────────────────────
# test_build_lc_messages_limits_history_window
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: confirm only the last 12 history messages are sent to the LLM.
# ────────────────────────────────────────────────────────────


def test_build_lc_messages_limits_history_window():
    long_history = [("user", f"msg-{i}") for i in range(20)]
    messages = build_lc_messages(long_history, "latest", None)
    human_messages = [m for m in messages if m.type == "human"]
    assert len(human_messages) <= 13


# ────────────────────────────────────────────────────────────
# test_demo_reply_mentions_layers_without_rag
# Endpoint: POST /chat/complete (internal — demo LLM mode)
# Use: offline demo reply explains LangChain and RAG when no context is found.
# ────────────────────────────────────────────────────────────


def test_demo_reply_mentions_layers_without_rag():
    text = demo_reply("hello", None)
    assert "Demo mode" in text
    assert "LangChain" in text
    assert "RAG" in text


# ────────────────────────────────────────────────────────────
# test_demo_reply_includes_rag_snippet_when_present
# Endpoint: POST /chat/complete (internal — demo LLM mode)
# Use: offline demo reply includes retrieved text when RAG context exists.
# ────────────────────────────────────────────────────────────


def test_demo_reply_includes_rag_snippet_when_present():
    text = demo_reply("hello", "annual leave is 14 days")
    assert "annual leave" in text
    assert "RAG context used" in text
