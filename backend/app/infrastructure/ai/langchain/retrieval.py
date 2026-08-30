"""
LangChain retrieval (RAG).

Find relevant document chunks for a user query.
Flow: embed query → search pgvector → return context text.

Fallback order:
  1. Vector search (semantic similarity)
  2. Keyword search (ILIKE match)
  3. First N chunks (only when strict mode is off)
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from app.core.config import get_settings
from app.infrastructure.ai.langchain.llm import get_embeddings
from app.infrastructure.database.models import Document, DocumentChunk
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.vector.pgvector import search_similar_chunks
from app.shared.constants import CHUNK_OVERLAP, CHUNK_SIZE
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

RetrievalFn = Callable[[AsyncSession, str, str, int], Awaitable[str | None]]


# ────────────────────────────────────────────────────────
# retrieve_context
# Internal — langchain / retrieval
# Main RAG entry point — tries each strategy until one returns text.
# ────────────────────────────────────────────────────────
async def retrieve_context(
    db: AsyncSession,
    user_id: str,
    query: str,
    k: int = 4,
) -> str | None:
    """Return joined chunk text for this user, or None if nothing matched."""
    # Try vector → keyword → fallback in order.
    for strategy in _retrieval_chain():
        try:
            result = await strategy(db, user_id, query, k)
        except Exception:
            logger.warning("Retrieval strategy %s failed", strategy.__name__)
            continue
        if result:
            return result
    return None


# ────────────────────────────────────────────────────────
# split_text
# Endpoint: POST /documents (internal)
# Splits uploaded text into overlapping chunks before storage.
# ────────────────────────────────────────────────────────
def split_text(
    text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Split document text into numbered chunks for embedding."""
    # Step 1: trim whitespace and reject empty input.
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]

    # Step 2: slide a window across the text with overlap.
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


class KnowledgeRetriever:
    """RetrieverPort — opens a DB session and runs retrieve_context."""

    # ────────────────────────────────────────────────────────
    # retrieve
    # Internal — langchain / retrieval
    # Called by agent.py to fetch RAG context for one user query.
    # ────────────────────────────────────────────────────────
    async def retrieve(self, user_id: str, query: str) -> str | None:
        """Search documents owned by this user and return context text."""
        async with SessionLocal() as db:
            return await retrieve_context(db, user_id, query)


# ────────────────────────────────────────────────────────
# _retrieval_chain
# Internal — langchain / retrieval
# Builds the ordered list of search strategies.
# ────────────────────────────────────────────────────────
def _retrieval_chain() -> tuple[RetrievalFn, ...]:
    """Return strategies in priority order."""
    chain: list[RetrievalFn] = [_vector_search, _keyword_search]
    # Add fallback only when strict mode allows answering without a match.
    if not get_settings().rag_strict_mode:
        chain.append(_fallback_chunks)
    return tuple(chain)


# ────────────────────────────────────────────────────────
# _vector_search
# Internal — langchain / retrieval
# Strategy 1 — semantic search via embeddings + pgvector.
# ────────────────────────────────────────────────────────
async def _vector_search(
    db: AsyncSession, user_id: str, query: str, k: int
) -> str | None:
    """Find nearest chunks by cosine distance."""
    # Step 1: get embedding client (None in demo mode).
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    # Step 2: convert query text to a vector.
    vector = await embeddings.aembed_query(query)
    # Step 3: search pgvector, scoped to this user.
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
# Internal — langchain / retrieval
# Strategy 2 — ILIKE keyword match (works without API key).
# ────────────────────────────────────────────────────────
async def _keyword_search(
    db: AsyncSession, user_id: str, query: str, k: int
) -> str | None:
    """Find chunks whose text contains the query keywords."""
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
# Internal — langchain / retrieval
# Strategy 3 — return first chunks (last resort, non-strict mode).
# ────────────────────────────────────────────────────────
async def _fallback_chunks(
    db: AsyncSession, user_id: str, _query: str, k: int
) -> str | None:
    """Return the first k chunks when no better match exists."""
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .order_by(DocumentChunk.chunk_index)
        .limit(k)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return "\n\n".join(rows) if rows else None
