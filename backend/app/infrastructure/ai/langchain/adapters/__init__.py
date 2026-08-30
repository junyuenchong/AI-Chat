"""LangChain adapters — compose ports for the application layer."""

from app.infrastructure.ai.langchain.adapters.chat_engine import build_chat_engine

__all__ = ["build_chat_engine"]
