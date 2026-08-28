"""
Conversation application helpers.

Creates new chat threads when the user sends their first message.
"""

from uuid import uuid4

from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.repositories.conversation_repository import (
    ConversationRepository,
)


# ────────────────────────────────────────────────────────
# create_new_conversation
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Inserts a new chat thread titled from the user's first message.
# ────────────────────────────────────────────────────────
async def create_new_conversation(
    conversations: ConversationRepository,
    user_id: str,
    title: str,
) -> Conversation:
    """Save a new conversation row and return it."""
    # Build a new thread row with a title derived from the first message.
    conversation = Conversation(
        id=str(uuid4()),
        user_id=user_id,
        title=title[:80] or "New conversation",  # Short title fits the sidebar.
    )
    # Insert the row and return it to the caller.
    await conversations.create(conversation)
    return conversation
