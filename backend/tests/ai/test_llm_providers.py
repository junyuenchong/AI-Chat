"""Unit tests for LangChain message mapping and demo LLM replies."""

from app.application.chat.helpers import build_llm_messages
from app.infrastructure.llm.demo.provider import demo_reply_text
from app.infrastructure.llm.langchain.message_mapper import to_lc_messages


def test_to_lc_messages_includes_system_and_user():
    domain_messages = build_llm_messages(
        history=[("user", "hi"), ("assistant", "hello")],
        user_message="what is RAG?",
        rag_context="chunk about leave policy",
    )
    messages = to_lc_messages(domain_messages)
    roles = [m.type for m in messages]
    assert roles[0] == "system"
    assert "chunk about leave policy" in messages[0].content
    assert roles[-1] == "human"
    assert messages[-1].content == "what is RAG?"


def test_to_lc_messages_limits_history_window():
    long_history = [("user", f"msg-{i}") for i in range(20)]
    domain_messages = build_llm_messages(long_history, "latest", None)
    messages = to_lc_messages(domain_messages)
    human_messages = [m for m in messages if m.type == "human"]
    assert len(human_messages) <= 13


def test_demo_reply_mentions_layers_without_rag():
    text = demo_reply_text("hello", None)
    assert "Demo mode" in text
    assert "LangChain" in text
    assert "RAG" in text


def test_demo_reply_includes_rag_snippet_when_present():
    text = demo_reply_text("hello", "annual leave is 14 days")
    assert "annual leave" in text
    assert "RAG context used" in text
