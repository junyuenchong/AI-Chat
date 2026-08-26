"""Background jobs: conversation summary + document embeddings."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.llm.providers import summarize_messages
from app.ai.rag.embeddings import get_embeddings
from app.ai.rag.service import split_text
from app.db.document import DocumentRepository
from app.db.session import SessionLocal
from app.models.conversation import Conversation
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


async def summarize_conversation(ctx: dict, conversation_id: str) -> str:
    """Write a short summary onto the conversation."""
    try:
        # ---------------------------------------------------------------------------
        # Load thread → LLM summary → save Conversation.summary.
        # ---------------------------------------------------------------------------
        async with SessionLocal() as db:
            conversation = await db.scalar(
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.messages))
            )
            if conversation is None:
                logger.warning("Summarize skipped; conversation %s missing", conversation_id)
                return "missing"
            transcript = "\n".join(f"{m.role}: {m.content}" for m in conversation.messages)
            summary = await summarize_messages(transcript)
            conversation.summary = summary
            await db.commit()

        logger.info("Summarized conversation %s", conversation_id)
        return summary
    except Exception:
        logger.exception("Summarize job failed for %s", conversation_id)
        return "error"


async def process_document(ctx: dict, document_id: str) -> int:
    """Embed document chunks into pgvector."""
    try:
        # ---------------------------------------------------------------------------
        # Re-chunk → embed → replace DocumentChunk rows (vectors nullable in demo).
        # ---------------------------------------------------------------------------
        async with SessionLocal() as db:
            document = await db.get(Document, document_id)
            if document is None:
                logger.warning("Embed job skipped; document %s missing", document_id)
                return 0
            chunks = split_text(document.content)
            embeddings = get_embeddings()
            try:
                vectors = await embeddings.aembed_documents(chunks) if embeddings is not None else None
            except Exception:
                logger.warning("Embedding API failed for document %s", document_id)
                vectors = None
            repo = DocumentRepository(db)
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
