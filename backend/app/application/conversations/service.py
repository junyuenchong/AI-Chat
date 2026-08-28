"""
Conversation application service.

Lists, loads, deletes, and creates chat threads (conversation history).
"""

from datetime import UTC, datetime

from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.conversations.dto.response import (
    ConversationDetailResponse,
    ConversationResponse,
)
from app.application.conversations.helpers import create_new_conversation
from app.application.conversations.mapper import ConversationMapper
from app.core.exceptions import (
    AppException,
    ConversationNotFound,
    database_error,
    require_found,
)
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.user import User
from app.infrastructure.database.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Stores the conversation repository for database access.
    # ────────────────────────────────────────────────────────
    def __init__(self, conversations: ConversationRepository) -> None:
        """Receive the conversation repository from FastAPI dependencies."""
        # Keep the repository on the service for all conversation queries.
        self.conversations = conversations

    # ────────────────────────────────────────────────────────
    # list_conversations
    # Endpoint: GET /conversations
    # Returns all chat threads for the sidebar.
    # ────────────────────────────────────────────────────────
    async def list_conversations(self, user: User) -> list[ConversationResponse]:
        """Load every conversation owned by this user."""
        try:
            # Fetch all threads belonging to the logged-in user.
            rows = await self.conversations.list_for_user(user.id)
        except SQLAlchemyError as exc:
            raise database_error("Could not load conversations.", exc) from exc

        # Map each row to the sidebar list response shape.
        return [ConversationMapper.conversation_to_list_item(row) for row in rows]

    # ────────────────────────────────────────────────────────
    # get_conversation
    # Endpoint: GET /conversations/{conversation_id}
    # Returns one thread with all messages for the chat pane.
    # ────────────────────────────────────────────────────────
    async def get_conversation(
        self, user: User, conversation_id: str
    ) -> ConversationDetailResponse:
        """Load a single conversation and its full message history."""
        try:
            # Load the thread and eager-load its messages.
            conversation = await self.conversations.get_with_messages(
                conversation_id, user.id
            )
        except SQLAlchemyError as exc:
            raise database_error("Could not load conversation.", exc) from exc

        # 404 when the thread is missing or belongs to another user.
        return ConversationMapper.conversation_with_messages(
            require_found(conversation, exc=ConversationNotFound)
        )

    # ────────────────────────────────────────────────────────
    # delete_conversation
    # Endpoint: DELETE /conversations/{conversation_id}
    # Removes a thread and all its messages from the sidebar.
    # ────────────────────────────────────────────────────────
    async def delete_conversation(self, user: User, conversation_id: str) -> None:
        """Delete one conversation and every message in it."""
        try:
            # Verify the thread exists and belongs to this user.
            conversation = await self.conversations.get_for_user(
                conversation_id, user.id
            )
        except SQLAlchemyError as exc:
            raise database_error("Could not delete conversation.", exc) from exc
        conversation = require_found(conversation, exc=ConversationNotFound)

        try:
            # Delete the row and commit the transaction.
            await self.conversations.delete(conversation)
            await self.conversations.db.commit()
        except SQLAlchemyError as exc:
            # Roll back if the delete fails partway through.
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
            # No id means this is the first message in a new thread.
            if not conversation_id:
                return await create_new_conversation(
                    self.conversations, user_id, title
                ), True

            # Load an existing thread and ensure it belongs to the user.
            conversation = await self.conversations.get_for_user(
                conversation_id, user_id
            )
            require_found(conversation, exc=ConversationNotFound)
            return conversation, False
        except AppException:
            # Let known app errors bubble up unchanged.
            raise
        except SQLAlchemyError as exc:
            # Roll back and wrap unexpected database failures.
            await self.conversations.db.rollback()
            raise database_error("Could not create conversation.", exc) from exc

    # ────────────────────────────────────────────────────────
    # update_last_activity
    # Endpoint: POST /chat/stream, POST /chat/complete (internal)
    # Updates the thread timestamp so the sidebar sorts by most recent message.
    # ────────────────────────────────────────────────────────
    async def update_last_activity(self, conversation: Conversation) -> None:
        """Set updated_at to now after a new message is saved."""
        # Bump the timestamp so the sidebar sorts this thread to the top.
        conversation.updated_at = datetime.now(UTC)
