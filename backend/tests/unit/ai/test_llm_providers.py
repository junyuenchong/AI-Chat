"""Unit tests for LangChain message mapping and demo LLM replies."""

from app.infrastructure.ai.langchain.chains import build_llm_messages
from app.infrastructure.ai.langchain.llm import demo_reply_text, to_lc_messages


def test_to_lc_messages_includes_system_and_user():
    domain_messages = build_llm_messages(
        history=[("user", "hi"), ("assistant", "hello")],
        user_message="what is SSE?",
    )
    messages = to_lc_messages(domain_messages)
    roles = [m.type for m in messages]
    assert roles[0] == "system"
    assert roles[-1] == "human"
    assert messages[-1].content == "what is SSE?"


def test_to_lc_messages_limits_history_window():
    long_history = [("user", f"msg-{i}") for i in range(20)]
    domain_messages = build_llm_messages(long_history, "latest")
    messages = to_lc_messages(domain_messages)
    human_messages = [m for m in messages if m.type == "human"]
    assert len(human_messages) <= 13


def test_demo_reply_mentions_demo_mode():
    text = demo_reply_text("hello")
    assert "Demo mode" in text
    assert "Question 2" in text


def test_demo_reply_echoes_user_message():
    text = demo_reply_text("hello there")
    assert "hello there" in text
