"""Chat orchestration: persist → RAG/LLM → stream/save."""

import json
import logging
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError

from app.ai.chat import run_chat, stream_chat
from app.api.v1.chat.dto import ChatCompleteResponse, ChatRequest
from app.api.v1.chat.mapping import ChatMapper
from app.clients.queue import get_queue
from app.clients.redis import get_redis
from app.core.config import get_settings
from app.core.errors import AppError, LLMError
from app.core.logging import enforce_rate_limit
from app.db.conversation import ConversationRepository
from app.db.message import MessageRepository
from app.db.session import SessionLocal
from app.models.user import User
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)


class ChatService:
    """Persist turns, run RAG/LLM, stream or complete."""

    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
    ) -> None:
        self.conversations = conversations
        self.messages = messages
        self.conversation_service = ConversationService(conversations)

    async def stream_chat(
        self,
        user: User,
        payload: ChatRequest,
        request: Request,
    ) -> AsyncIterator[dict]:
        """SSE path: rate-limit → save user → stream tokens → save assistant."""

        # ---------------------------------------------------------------------------
        # Rate limit — Redis INCR; fail open if Redis is down.
        # ---------------------------------------------------------------------------
        await enforce_rate_limit(get_redis(), user.id)
        incoming = payload.message.strip()
        if not incoming:
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "code": "VALIDATION_ERROR",
                        "message": "One or more fields are invalid.",
                        "fields": [{"field": "message", "message": "Message cannot be blank.", "type": "value_error"}],
                    }
                ),
            }
            return

        conversation_id = str(payload.conversation_id) if payload.conversation_id else None

        try:
            # ---------------------------------------------------------------------------
            # Dedicated SessionLocal — SSE outlives request-scoped get_db().
            # ---------------------------------------------------------------------------
            async with SessionLocal() as db:
                conversations = ConversationRepository(db)
                messages = MessageRepository(db)
                conversation_service = ConversationService(conversations)
                try:
                    conversation, created = await conversation_service.get_or_create(
                        user.id,
                        conversation_id,
                        incoming,
                    )
                except AppError as exc:
                    yield {
                        "event": "error",
                        "data": json.dumps(
                            {"code": exc.code, "message": exc.message, "fields": exc.fields}
                        ),
                    }
                    return

                # ---------------------------------------------------------------------------
                # Persist user turn before streaming so history is durable.
                # ---------------------------------------------------------------------------
                history = await messages.list_history(conversation.id)
                await messages.add(conversation.id, "user", incoming)
                await db.commit()

                # ---------------------------------------------------------------------------
                # RAG + LLM stream — map ai/chat events to SSE frames.
                # ---------------------------------------------------------------------------
                pieces: list[str] = []
                route = "direct"
                used_rag = False
                async for event_name, event_data in stream_chat(
                    db, user.id, incoming, history, payload.use_rag
                ):
                    if await request.is_disconnected():
                        return
                    if event_name == "error":
                        yield {"event": "error", "data": json.dumps({"code": "LLM_ERROR", "message": event_data})}
                        continue
                    if event_name == "route":
                        route = event_data
                        yield {
                            "event": "meta",
                            "data": json.dumps(
                                {
                                    "conversation_id": conversation.id,
                                    "llm": get_settings().llm_provider,
                                    "components": "langchain",
                                    "route": route,
                                }
                            ),
                        }
                    elif event_name == "rag":
                        used_rag = event_data == "1"
                    elif event_name == "token":
                        pieces.append(event_data)
                        yield {"event": "token", "data": json.dumps({"content": event_data})}

                # ---------------------------------------------------------------------------
                # Persist assistant reply after the stream finishes.
                # ---------------------------------------------------------------------------
                assistant_text = "".join(pieces).strip() or "I could not generate a reply. Please try again."
                await messages.add(conversation.id, "assistant", assistant_text)
                await conversation_service.touch(conversation)
                await db.commit()

                # ---------------------------------------------------------------------------
                # Background summary — every 4 messages (debounce later if busy).
                # ---------------------------------------------------------------------------
                count = await messages.count(conversation.id)
                queue = get_queue()
                if queue is not None and count >= 4 and count % 4 == 0:
                    try:
                        await queue.enqueue_job("summarize_conversation", conversation.id)
                    except Exception:
                        logger.warning("Could not enqueue summarize job for %s", conversation.id)

                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "conversation_id": conversation.id,
                            "content": assistant_text,
                            "route": route,
                            "rag": used_rag,
                        }
                    ),
                }
        except AppError as exc:
            yield {
                "event": "error",
                "data": json.dumps({"code": exc.code, "message": exc.message, "fields": exc.fields}),
            }
        except SQLAlchemyError:
            logger.exception("Chat stream database error")
            yield {
                "event": "error",
                "data": json.dumps({"code": "DATABASE_ERROR", "message": "Database is unavailable. Try again."}),
            }
        except Exception:
            logger.exception("Chat stream unhandled error")
            yield {
                "event": "error",
                "data": json.dumps({"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}),
            }

    async def complete_chat(self, user: User, payload: ChatRequest) -> ChatCompleteResponse:
        """Non-streaming path: persist → RAG/LLM → save."""
        await enforce_rate_limit(get_redis(), user.id)
        incoming = payload.message.strip()
        if not incoming:
            raise AppError(
                "One or more fields are invalid.",
                code="VALIDATION_ERROR",
                status_code=422,
                fields=[{"field": "message", "message": "Message cannot be blank.", "type": "value_error"}],
            )
        conversation_id = str(payload.conversation_id) if payload.conversation_id else None
        try:
            # ---------------------------------------------------------------------------
            # Same persist → agent → save path as stream (request-scoped DB).
            # ---------------------------------------------------------------------------
            conversation, _created = await self.conversation_service.get_or_create(
                user.id, conversation_id, incoming
            )
            history = await self.messages.list_history(conversation.id)
            await self.messages.add(conversation.id, "user", incoming)
            await self.conversations.db.commit()
            result = await run_chat(
                self.conversations.db, user.id, incoming, history, payload.use_rag
            )
            reply = (result.get("answer") or "").strip() or "I could not generate a reply. Please try again."
            await self.messages.add(conversation.id, "assistant", reply)
            await self.conversation_service.touch(conversation)
            await self.conversations.db.commit()
        except AppError:
            await self.conversations.db.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.conversations.db.rollback()
            raise AppError(
                "Could not save the chat message.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
        except Exception as exc:
            await self.conversations.db.rollback()
            raise LLMError("The language model failed. Try again.") from exc
        return ChatMapper.to_complete_response(
            conversation_id=conversation.id,
            content=reply,
            llm=get_settings().llm_provider,
        )
