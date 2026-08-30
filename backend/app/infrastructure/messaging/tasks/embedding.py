"""
Embedding helpers for background document jobs.
"""

import logging

from app.infrastructure.ai.langchain.llm import get_embeddings

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# embed_text_chunks
# Internal — background jobs
# Batch-embeds document chunks, or returns None when embeddings are unavailable.
# ────────────────────────────────────────────────────────
async def embed_text_chunks(chunks: list[str]) -> list[list[float]] | None:
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        return await embeddings.aembed_documents(chunks)
    except Exception:
        logger.warning("Embedding API failed for %s chunks", len(chunks))
        return None
