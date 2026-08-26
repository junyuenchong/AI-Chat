"""RAG package: chunk text, embed, search vectors, retrieve context.

One folder so ingest, chat, and background jobs share the same path.
"""

from app.ai.rag.embeddings import get_embeddings
from app.ai.rag.retrieve import retrieve_context
from app.ai.rag.service import split_text

__all__ = ["get_embeddings", "retrieve_context", "split_text"]
