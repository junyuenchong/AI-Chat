"""Prompt templates."""

from app.ai.prompts.chat import SYSTEM_PROMPT, with_rag_context
from app.ai.prompts.rag import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT

__all__ = [
    "SUMMARIZE_SYSTEM_PROMPT",
    "SUMMARIZE_USER_PROMPT",
    "SYSTEM_PROMPT",
    "with_rag_context",
]
