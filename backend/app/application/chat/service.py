"""
Chat application service.

Handles streaming and non-streaming AI chat — saves messages and calls the LLM.

Request path:
  api/v1/chat/router.py
    → application/chat/mapper.py
    → application/chat/service.py  (this file)
    → infrastructure/ai/langchain/adapters/chat_engine.py
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field

from app.application.chat.commands import ChatCommand, ChatCompleteResult
from app.application.conversations.service import ConversationService
from app.core.config import get_settings
from app.core.exceptions import AppException, LLMError, database_error
from app.domain.chat.ports import ChatEngine
from app.infrastructure.database.repositories.chat import MessageRepository
from app.infrastructure.database.repositories.conversation import ConversationRepository
from app.infrastructure.database.session import SessionLocal
from app.shared.constants import EMPTY_REPLY, LLM_FAILURE
from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ChatService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Wires up the chat engine and message storage.
    # ────────────────────────────────────────────────────────
    def __init__(
        self,
        chat_engine: ChatEngine,
        conversations: ConversationRepository,
        messages: MessageRepository,
    ) -> None:
        """Receive chat engine and repositories from FastAPI dependencies."""
        self.chat_engine = chat_engine
        self.conversations = conversations
        self.messages = messages
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
        incoming = command.message.strip()
        if not incoming:
            yield _build_blank_message_error()
            return

        try:
            # Step 1 — open a dedicated DB session (stream may outlive the request).
            async with SessionLocal() as db:
                conversations = ConversationRepository(db)
                messages = MessageRepository(db)
                conversation_service = ConversationService(conversations)

                try:
                    # Step 2 — find existing thread or create one from the first message.
                    (
                        conversation,
                        _created,
                    ) = await conversation_service.find_or_create_conversation(
                        command.user_id,
                        command.conversation_id,
                        incoming,
                    )
                except AppException as exc:
                    yield _build_app_error_event(exc.code, exc.message, exc.fields)
                    return

                # Step 3 — load history, save user message, commit before LLM call.
                history = await messages.list_history(conversation.id)
                await messages.add(conversation.id, "user", incoming)
                await db.commit()

                # Step 4 — stream tokens from LangChain and map to SSE frames.
                state = _StreamTurnState()
                mapper = _StreamEventMapper(conversation.id, state)
                yield _build_meta_event(mapper, "chat")
                async for (
                    event_name,
                    event_data,
                ) in self.chat_engine.generate_streaming_tokens(
                    incoming,
                    history,
                ):
                    if await request.is_disconnected():
                        return
                    frame = mapper.to_sse_frame(event_name, event_data)
                    if frame is not None:
                        yield frame

                # Step 5 — save assistant reply and bump thread activity.
                assistant_text = "".join(state.pieces).strip() or EMPTY_REPLY
                await messages.add(conversation.id, "assistant", assistant_text)
                await conversation_service.update_last_activity(conversation)
                await db.commit()

                # Step 6 — signal completion with full text for the UI.
                yield _build_done_event(conversation.id, assistant_text)
        except Exception as exc:
            if not isinstance(exc, AppException):
                logger.exception("Chat stream error: %s", exc.__class__.__name__)
            yield _build_error_from_exception(exc)

    # ────────────────────────────────────────────────────────
    # complete_chat
    # Endpoint: POST /chat/complete
    # Returns the full AI reply as one JSON response (no streaming).
    # ────────────────────────────────────────────────────────
    async def complete_chat(self, command: ChatCommand) -> ChatCompleteResult:
        """Save the user message, get one AI reply, save it, and return JSON."""
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
            # Step 1 — find or create the conversation thread.
            (
                conversation,
                _created,
            ) = await self.conversation_service.find_or_create_conversation(
                command.user_id,
                command.conversation_id,
                incoming,
            )

            # Step 2 — load history, save user message, commit before LLM call.
            history = await self.messages.list_history(conversation.id)
            await self.messages.add(conversation.id, "user", incoming)
            await self.conversations.db.commit()

            # Step 3 — get one full reply from LangChain (no streaming).
            result = await self.chat_engine.generate_full_reply(
                incoming,
                history,
            )
            reply = (result.get("answer") or "").strip() or EMPTY_REPLY

            # Step 4 — save assistant reply and return JSON result.
            await self.messages.add(conversation.id, "assistant", reply)
            await self.conversation_service.update_last_activity(conversation)
            await self.conversations.db.commit()
        except AppException:
            await self.conversations.db.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.conversations.db.rollback()
            raise database_error("Could not save the chat message.", exc) from exc
        except Exception as exc:
            await self.conversations.db.rollback()
            raise LLMError(LLM_FAILURE) from exc

        return ChatCompleteResult(
            conversation_id=conversation.id,
            content=reply,
            llm=get_settings().llm_provider,
        )


@dataclass
class _StreamTurnState:
    """Tracks accumulated tokens during one streamed reply."""

    pieces: list[str] = field(default_factory=list)


@dataclass
class _StreamEventMapper:
    """Converts internal stream events (token, error) into SSE frames."""

    conversation_id: str
    state: _StreamTurnState

    # ────────────────────────────────────────────────────────
    # to_sse_frame
    # Endpoint: POST /chat/stream (internal)
    # Routes an internal event name to the correct SSE frame builder.
    # ────────────────────────────────────────────────────────
    def to_sse_frame(self, event_name: str, event_data: str) -> dict | None:
        """Return an SSE frame for this event, or None if the event has no frame."""
        handler = _INTERNAL_EVENT_HANDLERS.get(event_name)
        if handler is None:
            return None
        return handler(self, event_data)


# ────────────────────────────────────────────────────────
# _build_error_event
# Endpoint: POST /chat/stream (internal)
# Builds a standard SSE error frame with code and message.
# ────────────────────────────────────────────────────────
def _build_error_event(
    code: str,
    message: str,
    *,
    fields: list[dict[str, str]] | None = None,
) -> dict:
    """Return an SSE error event the browser can display."""
    payload: dict = {"code": code, "message": message}
    if fields is not None:
        payload["fields"] = fields
    return {"event": "error", "data": json.dumps(payload)}


# ────────────────────────────────────────────────────────
# _build_blank_message_error
# Endpoint: POST /chat/stream (internal)
# Returns validation error when the user sends an empty message.
# ────────────────────────────────────────────────────────
def _build_blank_message_error() -> dict:
    """Return the same validation error shape as POST /chat/complete."""
    return _build_error_event(
        "VALIDATION_ERROR",
        "One or more fields are invalid.",
        fields=[
            {
                "field": "message",
                "message": "Message cannot be blank.",
                "type": "value_error",
            }
        ],
    )


# ────────────────────────────────────────────────────────
# _build_app_error_event
# Endpoint: POST /chat/stream (internal)
# Converts a domain error (AppException) into an SSE error frame.
# ────────────────────────────────────────────────────────
def _build_app_error_event(
    code: str, message: str, fields: list[dict[str, str]] | None = None
) -> dict:
    """Forward application error details to the streaming client."""
    return _build_error_event(code, message, fields=fields or [])


# ────────────────────────────────────────────────────────
# _build_done_event
# Endpoint: POST /chat/stream (internal)
# Sends the final event with the complete AI reply and metadata.
# ────────────────────────────────────────────────────────
def _build_done_event(conversation_id: str, content: str) -> dict:
    """Signal that streaming is finished and return the full assistant message."""
    return {
        "event": "done",
        "data": json.dumps(
            {
                "conversation_id": conversation_id,
                "content": content,
            }
        ),
    }


# ────────────────────────────────────────────────────────
# _build_error_from_exception
# Endpoint: POST /chat/stream (internal)
# Catches any unexpected error and returns a safe SSE error frame.
# ────────────────────────────────────────────────────────
def _build_error_from_exception(exc: Exception) -> dict:
    """Map known exceptions to specific errors; unknown ones become INTERNAL_ERROR."""
    for exc_type, handler in _STREAM_EXCEPTION_HANDLERS.items():
        if isinstance(exc, exc_type):
            return handler(exc)
    return _build_error_event("INTERNAL_ERROR", "An unexpected error occurred.")


# ────────────────────────────────────────────────────────
# _build_meta_event
# Endpoint: POST /chat/stream (internal)
# SSE meta/done helpers for the chat stream.
# ────────────────────────────────────────────────────────
def _build_meta_event(mapper: _StreamEventMapper, route: str) -> dict:
    """Emit meta event with conversation id and LLM provider."""
    return {
        "event": "meta",
        "data": json.dumps(
            {
                "conversation_id": mapper.conversation_id,
                "llm": get_settings().llm_provider,
                "components": "langchain",
                "route": route,
            }
        ),
    }


# ────────────────────────────────────────────────────────
# _build_llm_error_event
# Endpoint: POST /chat/stream (internal)
# Returns an error when the language model fails mid-stream.
# ────────────────────────────────────────────────────────
def _build_llm_error_event(_mapper: _StreamEventMapper, message: str) -> dict:
    """Emit LLM_ERROR so the UI can show a retry message."""
    return {
        "event": "error",
        "data": json.dumps({"code": "LLM_ERROR", "message": message}),
    }


# ────────────────────────────────────────────────────────
# _build_token_event
# Endpoint: POST /chat/stream (internal)
# Sends one AI token to the client and saves it to the reply buffer.
# ────────────────────────────────────────────────────────
def _build_token_event(mapper: _StreamEventMapper, token: str) -> dict:
    """Emit one token and append it to the in-memory full reply."""
    mapper.state.pieces.append(token)
    return {"event": "token", "data": json.dumps({"content": token})}


_INTERNAL_EVENT_HANDLERS: dict[
    str, Callable[[_StreamEventMapper, str], dict | None]
] = {
    "error": lambda m, data: _build_llm_error_event(m, data),
    "token": lambda m, data: _build_token_event(m, data),
}

_STREAM_EXCEPTION_HANDLERS: dict[type, Callable[[Exception], dict]] = {
    AppException: lambda exc: _build_app_error_event(exc.code, exc.message, exc.fields),  # type: ignore[attr-defined]
}


# ────────────────────────────────────────────────────────
# _register_stream_exception_handlers
# Internal — runs once at import time.
# Adds database error handling without circular imports.
# ────────────────────────────────────────────────────────
def _register_stream_exception_handlers() -> None:
    """Register SQLAlchemy handler after optional imports are available."""
    from sqlalchemy.exc import SQLAlchemyError

    _STREAM_EXCEPTION_HANDLERS[SQLAlchemyError] = lambda _exc: _build_error_event(
        "DATABASE_ERROR", "Database is unavailable. Try again."
    )


_register_stream_exception_handlers()
