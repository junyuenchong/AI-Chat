"""
LangChain wiring for the Q2 chat flow.

Request path:
  core/dependencies.py
    → infrastructure/ai/__init__.py  (this file)
    → infrastructure/ai/langchain/adapters/chat_engine.py
"""

from app.infrastructure.ai.langchain import ChatChain, build_chat_engine, build_llm_port

__all__ = ["ChatChain", "build_chat_engine", "build_llm_port"]
