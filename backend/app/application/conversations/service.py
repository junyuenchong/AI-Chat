"""
Conversation application service.

Lists, loads, deletes, and creates chat threads (conversation history).

Request path:
  api/v1/conversations/router.py
    → application/conversations/mapper.py
    → application/conversations/service.py  (this file)
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import (
    AppException,
    ConversationNotFound,
    database_error,
    require_found,
)
from app.infrastructure.database.models import Conversation, User
from app.infrastructure.database.repositories.conversation import ConversationRepository
from sqlalchemy.exc import SQLAlchemyError


# ────────────────────────────────────────────────────────
# _create_new_conversation
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Inserts a new chat thread titled from the user's first message.
# ────────────────────────────────────────────────────────
async def _create_new_conversation(
    conversations: ConversationRepository,
    user_id: str,
    title: str,
) -> Conversation:
    """Save a new conversation row and return it."""
    conversation = Conversation(
        id=str(uuid4()),
        user_id=user_id,
        title=title[:80] or "New conversation",
    )
    await conversations.create(conversation)
    return conversation


class ConversationService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Stores the conversation repository for database access.
    # ────────────────────────────────────────────────────────
    def __init__(self, conversations: ConversationRepository) -> None:
        """Receive the conversation repository from FastAPI dependencies."""
        self.conversations = conversations

    # ────────────────────────────────────────────────────────
    # list_conversations
    # Endpoint: GET /conversations
    # Returns all chat threads for the sidebar.
    # ────────────────────────────────────────────────────────
    async def list_conversations(self, user: User) -> list[Conversation]:
        """Load every conversation owned by this user."""
        try:
            return await self.conversations.list_for_user(user.id)
        except SQLAlchemyError as exc:
            raise database_error("Could not load conversations.", exc) from exc

    # ────────────────────────────────────────────────────────
    # get_conversation
    # Endpoint: GET /conversations/{conversation_id}
    # Returns one thread with all messages for the chat pane.
    # ────────────────────────────────────────────────────────
    async def get_conversation(self, user: User, conversation_id: str) -> Conversation:
        """Load a single conversation and its full message history."""
        try:
            # Step 1 — load thread + messages, scoped to this user.
            conversation = await self.conversations.get_with_messages(
                conversation_id, user.id
            )
        except SQLAlchemyError as exc:
            raise database_error("Could not load conversation.", exc) from exc
        return require_found(conversation, exc=ConversationNotFound)

    # ────────────────────────────────────────────────────────
    # delete_conversation
    # Endpoint: DELETE /conversations/{conversation_id}
    # Removes a thread and all its messages from the sidebar.
    # ────────────────────────────────────────────────────────
    async def delete_conversation(self, user: User, conversation_id: str) -> None:
        """Delete one conversation and every message in it."""
        try:
            # Step 1 — verify the thread belongs to this user.
            conversation = await self.conversations.get_for_user(
                conversation_id, user.id
            )
        except SQLAlchemyError as exc:
            raise database_error("Could not delete conversation.", exc) from exc
        conversation = require_found(conversation, exc=ConversationNotFound)

        try:
            # Step 2 — delete row and commit.
            await self.conversations.delete(conversation)
            await self.conversations.db.commit()
        except SQLAlchemyError as exc:
            await self.conversations.db.rollback()
            raise database_error("Could not delete conversation.", exc) from exc

    # ────────────────────────────────────────────────────────
    # find_or_create_conversation
    # Endpoint: POST /chat/stream, POST /chat/complete (internal)
    # Uses an existing thread id, or creates a new thread on first message.
    # ────────────────────────────────────────────────────────
    async def find_or_create_conversation(
        self,
        user_id: str,
        conversation_id: str | None,
        title: str,
    ) -> tuple[Conversation, bool]:
        """Return (conversation, was_created). True when a new thread was created."""
        try:
            # Step 1 — no id means first message in a new chat.
            if not conversation_id:
                return await _create_new_conversation(
                    self.conversations, user_id, title
                ), True

            # Step 2 — existing id must belong to this user.
            conversation = await self.conversations.get_for_user(
                conversation_id, user_id
            )
            require_found(conversation, exc=ConversationNotFound)
            return conversation, False
        except AppException:
            raise
        except SQLAlchemyError as exc:
            await self.conversations.db.rollback()
            raise database_error("Could not create conversation.", exc) from exc

    # ────────────────────────────────────────────────────────
    # update_last_activity
    # Endpoint: POST /chat/stream, POST /chat/complete (internal)
    # Updates the thread timestamp so the sidebar sorts by most recent message.
    # ────────────────────────────────────────────────────────
    async def update_last_activity(self, conversation: Conversation) -> None:
        """Set updated_at to now after a new message is saved."""
        conversation.updated_at = datetime.now(UTC)
