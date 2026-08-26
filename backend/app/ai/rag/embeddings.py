"""Embedding client (Gemini or OpenAI) — None in demo → keyword RAG fallback."""

from app.core.config import get_settings


def get_embeddings():
    """Build a LangChain embeddings client, or None in demo mode."""
    settings = get_settings()
    if not settings.llm_enabled:
        return None
    try:
        # ---------------------------------------------------------------------------
        # Same provider pick as chat LLM so vectors and chat stay consistent.
        # ---------------------------------------------------------------------------
        if settings.llm_provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(
                model=settings.gemini_embedding_model,
                google_api_key=settings.gemini_api_key,
            )
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.llm_embedding_model,
            api_key=settings.openai_api_key,
        )
    except Exception:
        return None
