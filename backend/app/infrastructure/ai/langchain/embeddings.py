"""
Embedding helpers with retry for LLM providers.
"""

import logging

from app.core.config import get_settings
from app.infrastructure.ai.langchain.llm import get_embeddings
from app.shared.retry import retry_async

logger = logging.getLogger(__name__)


def _retry_kwargs() -> dict[str, float | int]:
    cfg = get_settings()
    return {
        "max_attempts": cfg.llm_retry_max_attempts,
        "base_delay": cfg.llm_retry_base_delay_seconds,
        "max_delay": cfg.llm_retry_max_delay_seconds,
    }


async def embed_text_chunks(chunks: list[str]) -> list[list[float]] | None:
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        return await retry_async(
            lambda: embeddings.aembed_documents(chunks),
            label="embed documents",
            **_retry_kwargs(),
        )
    except Exception:
        logger.warning("Embedding API failed for %s chunks after retries", len(chunks))
        return None


async def embed_query(query: str) -> list[float] | None:
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        return await retry_async(
            lambda: embeddings.aembed_query(query),
            label="embed query",
            **_retry_kwargs(),
        )
    except Exception:
        logger.warning("Query embedding failed after retries")
        return None
