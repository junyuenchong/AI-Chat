"""
Embedding client.

Builds a LangChain embeddings client, or None in demo mode.
"""

from app.core.config import get_settings
from app.infrastructure.llm.provider_registry import build_embeddings


# ────────────────────────────────────────────────────────
# get_embeddings
# Internal — embeddings
# Builds a LangChain embeddings client, or None in demo mode.
# ────────────────────────────────────────────────────────
def get_embeddings():
    """Build a LangChain embeddings client, or None in demo mode."""
    # Resolve settings and delegate to the provider registry.
    return build_embeddings(get_settings())
