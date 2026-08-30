"""Conversation domain types."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NewConversation:
    """Input for creating a chat thread from the first user message."""

    user_id: str
    title: str
