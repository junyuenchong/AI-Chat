"""
LangChain infrastructure — Q2 chat core only.

Request path:
  infrastructure/ai/__init__.py
    → infrastructure/ai/langchain/__init__.py  (this file)

Layout:
  llm/        — model factory, provider, message mapping
  prompts/    — system and chat prompt templates
  chains/     — chat workflow (implements ChatEngine port)
  callbacks/  — token streaming helper
  adapters/   — wire LLM into ChatChain for DI
"""

from app.infrastructure.ai.langchain.adapters import build_chat_engine
from app.infrastructure.ai.langchain.chains import ChatChain
from app.infrastructure.ai.langchain.llm import build_llm_port

__all__ = [
    "ChatChain",
    "build_chat_engine",
    "build_llm_port",
]
