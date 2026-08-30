"""
Document processing background jobs.
"""

import logging

from app.infrastructure.ai.langchain.retrieval import split_text
from app.infrastructure.database.models import Document, DocumentChunk
from app.infrastructure.database.repositories.document import DocumentRepository
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.messaging.tasks.embedding import embed_text_chunks

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# process_document
# Internal — background jobs
# Chunks and embeds a document into pgvector after upload.
# ────────────────────────────────────────────────────────
async def process_document(ctx: dict, document_id: str) -> int:
    """Embed document chunks into pgvector."""
    try:
        async with SessionLocal() as db:
            document = await db.get(Document, document_id)
            if document is None:
                logger.warning("Embed job skipped; document %s missing", document_id)
                return 0
            chunks = split_text(document.content)
            vectors = await embed_text_chunks(chunks)
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
