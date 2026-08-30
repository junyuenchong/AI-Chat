"""Unit tests for prompt templates."""

from app.infrastructure.ai.langchain.prompts import SYSTEM_PROMPT


def test_system_prompt_is_non_empty():
    assert "assistant" in SYSTEM_PROMPT.lower()
