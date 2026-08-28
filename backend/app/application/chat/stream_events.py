"""
Chat stream events.

Builds Server-Sent Event (SSE) frames for the live streaming chat endpoint.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.exceptions import AppException


@dataclass
class StreamTurnState:
    """Tracks route, RAG usage, and accumulated tokens during one streamed reply."""

    route: str = "direct"
    used_rag: bool = False
    pieces: list[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────
# build_error_event
# Endpoint: POST /chat/stream (internal)
# Builds a standard SSE error frame with code and message.
# ────────────────────────────────────────────────────────
def build_error_event(
    code: str,
    message: str,
    *,
    fields: list[dict[str, str]] | None = None,
) -> dict:
    """Return an SSE error event the browser can display."""
    # Build the JSON payload the client will parse.
    payload: dict = {"code": code, "message": message}
    if fields is not None:
        # Include field-level validation details when present.
        payload["fields"] = fields
    return {"event": "error", "data": json.dumps(payload)}


# ────────────────────────────────────────────────────────
# build_blank_message_error
# Endpoint: POST /chat/stream (internal)
# Returns validation error when the user sends an empty message.
# ────────────────────────────────────────────────────────
def build_blank_message_error() -> dict:
    """Return the same validation error shape as POST /chat/complete."""
    # Reuse the standard error builder with a message field error.
    return build_error_event(
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
# build_app_error_event
# Endpoint: POST /chat/stream (internal)
# Converts a domain error (AppException) into an SSE error frame.
# ────────────────────────────────────────────────────────
def build_app_error_event(
    code: str, message: str, fields: list[dict[str, str]] | None = None
) -> dict:
    """Forward application error details to the streaming client."""
    # Default to an empty fields list when none were provided.
    return build_error_event(code, message, fields=fields or [])


# ────────────────────────────────────────────────────────
# build_done_event
# Endpoint: POST /chat/stream (internal)
# Sends the final event with the complete AI reply and metadata.
# ────────────────────────────────────────────────────────
def build_done_event(
    conversation_id: str, content: str, route: str, used_rag: bool
) -> dict:
    """Signal that streaming is finished and return the full assistant message."""
    return {
        "event": "done",
        "data": json.dumps(
            {
                "conversation_id": conversation_id,
                "content": content,
                "route": route,
                "rag": used_rag,
            }
        ),
    }


# ────────────────────────────────────────────────────────
# build_error_from_exception
# Endpoint: POST /chat/stream (internal)
# Catches any unexpected error and returns a safe SSE error frame.
# ────────────────────────────────────────────────────────
def build_error_from_exception(exc: Exception) -> dict:
    """Map known exceptions to specific errors; unknown ones become INTERNAL_ERROR."""
    # Walk registered handlers for a matching exception type.
    for exc_type, handler in _STREAM_EXCEPTION_HANDLERS.items():
        if isinstance(exc, exc_type):
            return handler(exc)
    # Fall back to a generic internal error for anything unknown.
    return build_error_event("INTERNAL_ERROR", "An unexpected error occurred.")


# ────────────────────────────────────────────────────────
# _build_meta_event
# Endpoint: POST /chat/stream (internal)
# Tells the client whether the reply used RAG or went direct to the LLM.
# ────────────────────────────────────────────────────────
def _build_meta_event(mapper: StreamEventMapper, route: str) -> dict:
    """Emit meta event with conversation id, LLM provider, and route."""
    # Remember the route on turn state for the final done event.
    mapper.state.route = route
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
def _build_llm_error_event(_mapper: StreamEventMapper, message: str) -> dict:
    """Emit LLM_ERROR so the UI can show a retry message."""
    return {
        "event": "error",
        "data": json.dumps({"code": "LLM_ERROR", "message": message}),
    }


# ────────────────────────────────────────────────────────
# _record_rag_usage
# Endpoint: POST /chat/stream (internal)
# Records whether knowledge-base search returned results (no SSE frame sent).
# ────────────────────────────────────────────────────────
def _record_rag_usage(mapper: StreamEventMapper, flag: str) -> None:
    """Update state from rag flag ('1' = found context, '0' = none)."""
    # Store whether retrieval found usable context for this turn.
    mapper.state.used_rag = flag == "1"


# ────────────────────────────────────────────────────────
# _build_token_event
# Endpoint: POST /chat/stream (internal)
# Sends one AI token to the client and saves it to the reply buffer.
# ────────────────────────────────────────────────────────
def _build_token_event(mapper: StreamEventMapper, token: str) -> dict:
    """Emit one token and append it to the in-memory full reply."""
    # Accumulate tokens so the service can save the full reply later.
    mapper.state.pieces.append(token)
    return {"event": "token", "data": json.dumps({"content": token})}


@dataclass
class StreamEventMapper:
    """Converts internal stream events (route, token, error) into SSE frames."""

    conversation_id: str
    state: StreamTurnState

    # ────────────────────────────────────────────────────────
    # to_sse_frame
    # Endpoint: POST /chat/stream (internal)
    # Routes an internal event name to the correct SSE frame builder.
    # ────────────────────────────────────────────────────────
    def to_sse_frame(self, event_name: str, event_data: str) -> dict | None:
        """Return an SSE frame for this event, or None if the event has no frame."""
        # Look up the handler for this internal event name.
        handler = _INTERNAL_EVENT_HANDLERS.get(event_name)
        if handler is None:
            # Some events (like rag) only update state and emit no frame.
            return None
        return handler(self, event_data)


_INTERNAL_EVENT_HANDLERS: dict[str, Callable[[StreamEventMapper, str], dict | None]] = {
    "error": lambda m, data: _build_llm_error_event(m, data),
    "route": lambda m, data: _build_meta_event(m, data),
    "rag": lambda m, data: _record_rag_usage(m, data) or None,
    "token": lambda m, data: _build_token_event(m, data),
}

_STREAM_EXCEPTION_HANDLERS: dict[type, Callable[[Exception], dict]] = {
    AppException: lambda exc: build_app_error_event(exc.code, exc.message, exc.fields),  # type: ignore[attr-defined]
}


# ────────────────────────────────────────────────────────
# _register_exception_handlers
# Internal — runs once at import time.
# Adds database error handling without circular imports.
# ────────────────────────────────────────────────────────
def _register_exception_handlers() -> None:
    """Register SQLAlchemy handler after optional imports are available."""
    # Import here to avoid circular imports at module load time.
    from sqlalchemy.exc import SQLAlchemyError

    # Map database errors to a user-friendly SSE error frame.
    _STREAM_EXCEPTION_HANDLERS[SQLAlchemyError] = lambda _exc: build_error_event(
        "DATABASE_ERROR", "Database is unavailable. Try again."
    )


_register_exception_handlers()
