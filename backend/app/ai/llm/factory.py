"""LLM provider factory: Gemini, OpenAI, or None (demo mode)."""

from app.core.config import get_settings


def get_chat_model():
    """Return a LangChain chat model, or None when no API key is set."""
    settings = get_settings()
    if not settings.llm_enabled:
        return None
    try:
        # ---------------------------------------------------------------------------
        # Provider — Gemini preferred when both keys exist (matches Settings.llm_provider).
        # ---------------------------------------------------------------------------
        if settings.llm_provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.4,
                streaming=True,
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0.4,
            streaming=True,
        )
    except Exception:
        # Import / client errors → demo path in providers.py.
        return None
