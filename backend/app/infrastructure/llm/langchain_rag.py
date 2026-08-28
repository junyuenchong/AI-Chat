"""
LangChain RAG retriever.

Concrete implementation of RetrieverPort using pgvector.
"""

from app.core.database import SessionLocal
from app.infrastructure.vectorstore.retriever import retrieve_context


class LangChainRetriever:
    """RetrieverPort — opens its own DB session; application stays ORM-free."""

    # ────────────────────────────────────────────────────────
    # retrieve
    # Internal — RAG retriever
    # Fetches relevant knowledge chunks for the given user and query.
    # ────────────────────────────────────────────────────────
    async def retrieve(self, user_id: str, query: str) -> str | None:
        # Open a short-lived DB session so the application layer stays ORM-free.
        async with SessionLocal() as db:
            return await retrieve_context(db, user_id, query)
