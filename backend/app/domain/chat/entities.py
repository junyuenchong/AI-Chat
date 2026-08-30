"""
Chat domain entities.

Framework-agnostic types for the chat use case.
"""

from dataclasses import dataclass
from typing import TypedDict


@dataclass(frozen=True, slots=True)
class ChatCommand:
    """Application input for one chat turn."""

    user_id: str
    message: str
    conversation_id: str | None


@dataclass(frozen=True, slots=True)
class ChatCompleteResult:
    """Application result for one non-streaming chat turn."""

    conversation_id: str
    content: str
    llm: str


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatResult(TypedDict):
    answer: str
