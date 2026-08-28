"""
Chat domain entities.

Framework-agnostic types for the chat use case.
"""

from dataclasses import dataclass
from typing import TypedDict


# ────────────────────────────────────────────────────────
# ChatCommand
# Internal — domain layer
# Immutable input for one chat turn (user, message, conversation, RAG flag).
# ────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class ChatCommand:
    """Application input for one chat turn."""

    user_id: str
    message: str
    conversation_id: str | None
    use_rag: bool


# ────────────────────────────────────────────────────────
# ChatMessage
# Internal — domain layer
# One message in the LLM conversation (role plus text content).
# ────────────────────────────────────────────────────────
class ChatMessage(TypedDict):
    role: str
    content: str


# ────────────────────────────────────────────────────────
# ChatResult
# Internal — domain layer
# Outcome of a non-streaming chat turn (route, RAG context, answer).
# ────────────────────────────────────────────────────────
class ChatResult(TypedDict):
    """Result of a non-streaming chat turn."""

    route: str
    rag_context: str | None
    answer: str
