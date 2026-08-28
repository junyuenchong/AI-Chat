"""
Background jobs.

ARQ tasks for conversation summaries and document embeddings.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.document import Document, DocumentChunk
from app.infrastructure.database.repositories.document_repository import (
    DocumentRepository,
)
from app.infrastructure.llm.factory import build_llm_port
from app.infrastructure.vectorstore.embeddings import get_embeddings
from app.infrastructure.vectorstore.retriever import split_text

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
            # Load conversation with messages eagerly for transcript building.
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
            # Flatten message history into a single transcript string.
            transcript = "\n".join(
                f"{m.role}: {m.content}" for m in conversation.messages
            )
            summary = await build_llm_port().summarize(transcript)
            conversation.summary = summary
            await db.commit()

        logger.info("Summarized conversation %s", conversation_id)
        return summary
    except Exception:
        logger.exception("Summarize job failed for %s", conversation_id)
        return "error"


# ────────────────────────────────────────────────────────
# process_document
# Internal — background jobs
# Embeds document chunks into pgvector after upload.
# ────────────────────────────────────────────────────────
async def process_document(ctx: dict, document_id: str) -> int:
    """Embed document chunks into pgvector."""
    try:
        async with SessionLocal() as db:
            document = await db.get(Document, document_id)
            if document is None:
                logger.warning("Embed job skipped; document %s missing", document_id)
                return 0
            # Split raw document text into overlapping chunks.
            chunks = split_text(document.content)
            embeddings = get_embeddings()
            try:
                # Batch-embed all chunks when an API client is available.
                vectors = (
                    await embeddings.aembed_documents(chunks)
                    if embeddings is not None
                    else None
                )
            except Exception:
                logger.warning("Embedding API failed for document %s", document_id)
                vectors = None
            repo = DocumentRepository(db)
            # Delete then insert so re-embed jobs stay idempotent.
            await repo.replace_chunks(
                document_id,
                [
                    DocumentChunk(
                        document_id=document_id,
                        chunk_index=i,
                        content=chunk,
                        embedding=vectors[i] if vectors else None,
                    )
                    for i, chunk in enumerate(chunks)
                ],
            )
            await db.commit()

        logger.info("Processed document %s (%s chunks)", document_id, len(chunks))
        return len(chunks)
    except Exception:
        logger.exception("Embed job failed for %s", document_id)
        return 0
