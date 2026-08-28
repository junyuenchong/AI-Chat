"""
Knowledge retriever.

RAG context retrieval — rule chain: vector → keyword → fallback chunks.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.database.models.document import Document, DocumentChunk
from app.infrastructure.vectorstore.embeddings import get_embeddings

logger = logging.getLogger(__name__)

RetrievalFn = Callable[[AsyncSession, str, str, int], Awaitable[str | None]]


# ────────────────────────────────────────────────────────
# retrieve_context
# Internal — knowledge retrieval
# Returns joined chunk text for a user query, or None if nothing matches.
# ────────────────────────────────────────────────────────
async def retrieve_context(
    db: AsyncSession,
    user_id: str,
    query: str,
    k: int = 4,
) -> str | None:
    """Return joined chunk text, or None if the user has no documents."""
    for strategy in _retrieval_chain():
        try:
            result = await strategy(db, user_id, query, k)
        except Exception:
            logger.warning("Retrieval strategy %s failed", strategy.__name__)
            continue
        if result:
            return result
    return None


def _retrieval_chain() -> tuple[RetrievalFn, ...]:
    """Vector + keyword always; fallback chunks only in hybrid (non-strict) mode."""
    chain: list[RetrievalFn] = [_vector_search, _keyword_search]
    if not get_settings().rag_strict_mode:
        chain.append(_fallback_chunks)
    return tuple(chain)


# ────────────────────────────────────────────────────────
# search_similar_chunks
# Internal — knowledge retrieval
# Returns top-k chunk texts by cosine distance for one user.
# ────────────────────────────────────────────────────────
async def search_similar_chunks(
    db: AsyncSession,
    user_id: str,
    vector: list[float],
    k: int = 4,
    *,
    max_distance: float | None = None,
) -> list[str]:
    """Return top-k chunk texts by cosine distance for this user only."""
    distance = DocumentChunk.embedding.cosine_distance(vector)
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .where(DocumentChunk.embedding.is_not(None))
    )
    if max_distance is not None:
        stmt = stmt.where(distance <= max_distance)
    stmt = stmt.order_by(distance).limit(k)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


# ────────────────────────────────────────────────────────
# split_text
# Internal — knowledge retrieval
# Splits raw document text into overlapping chunks for ingest and embed jobs.
# ────────────────────────────────────────────────────────
def split_text(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    """Chunk raw text. Used by knowledge ingest and the embed job."""
    cleaned = text.strip()
    if not cleaned:
        return []
    # Short documents fit in a single chunk.
    if len(cleaned) <= size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        # Slice a window of `size` characters from the current offset.
        end = min(start + size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        # Advance with overlap so context spans chunk boundaries.
        start = max(end - overlap, start + 1)
    return chunks


# ────────────────────────────────────────────────────────
# _vector_search
# Internal — knowledge retrieval
# Embeds the query and retrieves the nearest vector chunks.
# ────────────────────────────────────────────────────────
async def _vector_search(
    db: AsyncSession, user_id: str, query: str, k: int
) -> str | None:
    embeddings = get_embeddings()
    if embeddings is None:
        # No embedding client — skip vector search in demo mode.
        return None
    # Embed the user query, then find nearest chunks by cosine distance.
    vector = await embeddings.aembed_query(query)
    rows = await search_similar_chunks(
        db,
        user_id,
        vector,
        k=k,
        max_distance=get_settings().rag_max_distance,
    )
    return "\n\n".join(rows) if rows else None


# ────────────────────────────────────────────────────────
# _keyword_search
# Internal — knowledge retrieval
# Finds chunks whose text matches a case-insensitive keyword pattern.
# ────────────────────────────────────────────────────────
async def _keyword_search(
    db: AsyncSession, user_id: str, query: str, k: int
) -> str | None:
    # Build a case-insensitive LIKE pattern from the first 80 chars of the query.
    like = f"%{query[:80].strip()}%"
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .where(DocumentChunk.content.ilike(like))
        .limit(k)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return "\n\n".join(rows) if rows else None


# ────────────────────────────────────────────────────────
# _fallback_chunks
# Internal — knowledge retrieval
# Returns the earliest stored chunks when vector and keyword search miss.
# ────────────────────────────────────────────────────────
async def _fallback_chunks(
    db: AsyncSession, user_id: str, _query: str, k: int
) -> str | None:
    # Return the first stored chunks in document order as a last resort.
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .order_by(DocumentChunk.chunk_index)
        .limit(k)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return "\n\n".join(rows) if rows else None
