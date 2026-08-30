"""
Maintenance background jobs (summaries, housekeeping).
"""

import logging

from app.infrastructure.database.models import Conversation
from app.infrastructure.database.session import SessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# summarize_conversation
# Internal — background jobs
# Writes a short summary onto a conversation after enough messages.
# ────────────────────────────────────────────────────────
async def summarize_conversation(ctx: dict, conversation_id: str) -> str:
    """Write a short summary onto the conversation."""
    try:
        async with SessionLocal() as db:
            conversation = await db.scalar(
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.messages))
            )
            if conversation is None:
                logger.warning(
                    "Summarize skipped; conversation %s missing", conversation_id
                )
                return "missing"
            transcript = "\n".join(
                f"{m.role}: {m.content}" for m in conversation.messages
            )
            from app.infrastructure.ai.langchain.agent import summarize_transcript

            summary = await summarize_transcript(transcript)
            conversation.summary = summary
            await db.commit()

        logger.info("Summarized conversation %s", conversation_id)
        return summary
    except Exception:
        logger.exception("Summarize job failed for %s", conversation_id)
        return "error"
