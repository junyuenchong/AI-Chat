"""
Chat application service.

Handles streaming and non-streaming AI chat — saves messages and calls the LLM.
"""

import logging
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.chat.dto.response import ChatCompleteResponse
from app.application.chat.commands import ChatCommand
from app.application.chat.helpers import (
    EMPTY_REPLY,
    LLM_FAILURE,
    generate_full_reply,
    generate_streaming_tokens,
)
from app.application.chat.mapper import ChatMapper
from app.application.chat.stream_events import (
    StreamEventMapper,
    StreamTurnState,
    build_app_error_event,
    build_blank_message_error,
    build_done_event,
    build_error_from_exception,
)
from app.application.conversations.service import ConversationService
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.exceptions import AppException, LLMError, database_error
from app.core.logging import enforce_rate_limit
from app.domain.chat.ports import LLMPort, RetrieverPort
from app.infrastructure.cache.redis import get_redis
from app.infrastructure.database.repositories.conversation_repository import (
    ConversationRepository,
    MessageRepository,
)
from app.infrastructure.queue.queue import get_queue

logger = logging.getLogger(__name__)


class ChatService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Wires up the LLM, knowledge search, and message storage.
    # ────────────────────────────────────────────────────────
    def __init__(
        self,
        llm: LLMPort,
        retriever: RetrieverPort,
        conversations: ConversationRepository,
        messages: MessageRepository,
    ) -> None:
        """Receive AI ports and repositories from FastAPI dependencies."""
        # Store AI and persistence dependencies for chat turns.
        self.llm = llm
        self.retriever = retriever
        self.conversations = conversations
        self.messages = messages
        # Reuse conversation helpers for thread lookup and creation.
        self.conversation_service = ConversationService(conversations)

    # ────────────────────────────────────────────────────────
    # stream_chat
    # Endpoint: POST /chat/stream
    # Streams AI reply tokens live to the browser (Server-Sent Events).
    # ────────────────────────────────────────────────────────
    async def stream_chat(
        self,
        command: ChatCommand,
        request: Request,
    ) -> AsyncIterator[dict]:
        """Save the user message, stream AI tokens, then save the assistant reply."""
        # Throttle how often this user can send messages.
        await enforce_rate_limit(get_redis(), command.user_id)

        # Reject blank messages before touching the database.
        incoming = command.message.strip()
        if not incoming:
            yield build_blank_message_error()
            return

        try:
            # Stream may outlive the request — use a dedicated DB session.
            async with SessionLocal() as db:
                # Build repositories bound to this long-lived session.
                conversations = ConversationRepository(db)
                messages = MessageRepository(db)
                conversation_service = ConversationService(conversations)

                try:
                    # Open an existing thread or start a new one from the first message.
                    (
                        conversation,
                        _created,
                    ) = await conversation_service.find_or_create_conversation(
                        command.user_id,
                        command.conversation_id,
                        incoming,
                    )
                except AppException as exc:
                    # Surface validation or not-found errors as SSE frames.
                    yield build_app_error_event(exc.code, exc.message, exc.fields)
                    return

                # Load prior messages, then persist the new user turn.
                history = await messages.list_history(conversation.id)
                await messages.add(conversation.id, "user", incoming)
                await db.commit()

                # Track streamed tokens and map internal events to SSE frames.
                state = StreamTurnState()
                mapper = StreamEventMapper(conversation.id, state)
                async for event_name, event_data in generate_streaming_tokens(
                    self.llm,
                    self.retriever,
                    command.user_id,
                    incoming,
                    history,
                    command.use_rag,
                ):
                    # Stop streaming if the client disconnected.
                    if await request.is_disconnected():
                        return
                    frame = mapper.to_sse_frame(event_name, event_data)
                    if frame is not None:
                        yield frame

                # Join streamed tokens into the final assistant message.
                assistant_text = "".join(state.pieces).strip() or EMPTY_REPLY
                await messages.add(conversation.id, "assistant", assistant_text)
                await conversation_service.update_last_activity(conversation)
                await db.commit()

                # Queue a background summary every four messages.
                count = await messages.count(conversation.id)
                queue = get_queue()
                if queue is not None and count >= 4 and count % 4 == 0:
                    try:
                        await queue.enqueue_job(
                            "summarize_conversation", conversation.id
                        )
                    except Exception:
                        logger.warning(
                            "Could not enqueue summarize job for %s", conversation.id
                        )

                # Send the closing event with the full reply and metadata.
                yield build_done_event(
                    conversation.id, assistant_text, state.route, state.used_rag
                )
        except Exception as exc:
            # Log unexpected failures, then return a safe SSE error.
            if not isinstance(exc, AppException):
                logger.exception("Chat stream error: %s", exc.__class__.__name__)
            yield build_error_from_exception(exc)

    # ────────────────────────────────────────────────────────
    # complete_chat
    # Endpoint: POST /chat/complete
    # Returns the full AI reply as one JSON response (no streaming).
    # ────────────────────────────────────────────────────────
    async def complete_chat(self, command: ChatCommand) -> ChatCompleteResponse:
        """Save the user message, get one AI reply, save it, and return JSON."""
        # Throttle how often this user can send messages.
        await enforce_rate_limit(get_redis(), command.user_id)

        # Reject blank messages with the same validation shape as streaming.
        incoming = command.message.strip()
        if not incoming:
            raise AppException(
                "One or more fields are invalid.",
                code="VALIDATION_ERROR",
                status_code=422,
                fields=[
                    {
                        "field": "message",
                        "message": "Message cannot be blank.",
                        "type": "value_error",
                    }
                ],
            )

        try:
            # Resolve the conversation thread for this message.
            (
                conversation,
                _created,
            ) = await self.conversation_service.find_or_create_conversation(
                command.user_id,
                command.conversation_id,
                incoming,
            )

            # Save the user message before calling the LLM.
            history = await self.messages.list_history(conversation.id)
            await self.messages.add(conversation.id, "user", incoming)
            await self.conversations.db.commit()

            # Generate one full reply (with optional RAG).
            result = await generate_full_reply(
                self.llm,
                self.retriever,
                command.user_id,
                incoming,
                history,
                command.use_rag,
            )
            reply = (result.get("answer") or "").strip() or EMPTY_REPLY

            # Persist the assistant reply and bump thread activity.
            await self.messages.add(conversation.id, "assistant", reply)
            await self.conversation_service.update_last_activity(conversation)
            await self.conversations.db.commit()
        except AppException:
            # Re-raise known app errors after rolling back.
            await self.conversations.db.rollback()
            raise
        except SQLAlchemyError as exc:
            # Wrap database failures in a consistent error type.
            await self.conversations.db.rollback()
            raise database_error("Could not save the chat message.", exc) from exc
        except Exception as exc:
            # Treat any other failure as an LLM error for the client.
            await self.conversations.db.rollback()
            raise LLMError(LLM_FAILURE) from exc

        # Return the completed reply as JSON.
        return ChatMapper.reply_to_response(
            conversation_id=conversation.id,
            content=reply,
            llm=get_settings().llm_provider,
        )
