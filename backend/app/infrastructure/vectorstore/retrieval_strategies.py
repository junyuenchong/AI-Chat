"""
RAG retrieval strategies.

Alternate strategy chain — vector → keyword → fallback.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.document import Document, DocumentChunk
from app.infrastructure.vectorstore.embeddings import get_embeddings

logger = logging.getLogger(__name__)

RetrieverFn = Callable[[AsyncSession, str, str, int], Awaitable[str | None]]


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
) -> list[str]:
    # Rank embedded chunks by cosine distance, scoped to this user.
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(DocumentChunk.embedding.cosine_distance(vector))
        .limit(k)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


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
        return None
    # Embed the query, then fetch the nearest chunk texts.
    vector = await embeddings.aembed_query(query)
    rows = await search_similar_chunks(db, user_id, vector, k=k)
    return "\n\n".join(rows) if rows else None


# ────────────────────────────────────────────────────────
# _keyword_search
# Internal — knowledge retrieval
# Finds chunks whose text matches a case-insensitive keyword pattern.
# ────────────────────────────────────────────────────────
async def _keyword_search(
    db: AsyncSession, user_id: str, query: str, k: int
) -> str | None:
    # Case-insensitive substring match on chunk content.
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
# _first_chunks_fallback
# Internal — knowledge retrieval
# Returns the earliest stored chunks when vector and keyword search miss.
# ────────────────────────────────────────────────────────
async def _first_chunks_fallback(
    db: AsyncSession, user_id: str, _query: str, k: int
) -> str | None:
    # Last resort — return the earliest chunks in storage order.
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .order_by(DocumentChunk.chunk_index)
        .limit(k)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return "\n\n".join(rows) if rows else None


_RETRIEVAL_CHAIN: tuple[RetrieverFn, ...] = (
    _vector_search,
    _keyword_search,
    _first_chunks_fallback,
)


# ────────────────────────────────────────────────────────
# retrieve_with_strategies
# Internal — knowledge retrieval
# Runs the retrieval strategy chain until one strategy returns context.
# ────────────────────────────────────────────────────────
async def retrieve_with_strategies(
    db: AsyncSession,
    user_id: str,
    query: str,
    k: int = 4,
) -> str | None:
    # Try each strategy in order until one returns non-empty context.
    for strategy in _RETRIEVAL_CHAIN:
        try:
            result = await strategy(db, user_id, query, k)
            if result:
                return result
        except Exception:
            logger.warning("Retrieval strategy %s failed", strategy.__name__)
    return None
