"""Retrieve RAG context for a user query (Knowledge / Chunks)."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.embeddings import get_embeddings
from app.ai.rag.pgvector import search_similar_chunks
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


async def retrieve_context(
    db: AsyncSession,
    user_id: str,
    query: str,
    k: int = 4,
) -> str | None:
    """Return joined chunk text, or None if the user has no documents."""

    # ---------------------------------------------------------------------------
    # 1) Vector search (pgvector) when embeddings client is available.
    # ---------------------------------------------------------------------------
    embeddings = get_embeddings()
    if embeddings is not None:
        try:
            vector = await embeddings.aembed_query(query)
            rows = await search_similar_chunks(db, user_id, vector, k=k)
            if rows:
                return "\n\n".join(rows)
        except Exception:
            logger.warning("Vector retrieval failed; using keyword fallback.")

    # ---------------------------------------------------------------------------
    # 2) Keyword match — works in demo mode without an API key.
    # ---------------------------------------------------------------------------
    like = f"%{query[:80].strip()}%"
    try:
        stmt = (
            select(DocumentChunk.content)
            .join(Document)
            .where(Document.user_id == user_id)
            .where(DocumentChunk.content.ilike(like))
            .limit(k)
        )
        rows = (await db.execute(stmt)).scalars().all()
        if rows:
            return "\n\n".join(rows)

        # ---------------------------------------------------------------------------
        # 3) Fallback — first chunks so RAG still has something to cite.
        # ---------------------------------------------------------------------------
        fallback = (
            select(DocumentChunk.content)
            .join(Document)
            .where(Document.user_id == user_id)
            .order_by(DocumentChunk.chunk_index)
            .limit(k)
        )
        rows = (await db.execute(fallback)).scalars().all()
        return "\n\n".join(rows) if rows else None
    except Exception:
        logger.warning("Keyword retrieval failed.")
        return None
