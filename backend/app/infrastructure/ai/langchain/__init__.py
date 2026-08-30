"""
LangChain package.

Five files, five responsibilities:
  llm.py       — connect to LLM + embeddings
  prompts.py   — how the AI should answer
  retrieval.py — RAG (embed → search → context)
  tools.py     — callable tools
  agent.py     — orchestration
"""

from app.infrastructure.ai.langchain.agent import ChatAgent
from app.infrastructure.ai.langchain.llm import build_llm_port
from app.infrastructure.ai.langchain.retrieval import KnowledgeRetriever

__all__ = ["ChatAgent", "KnowledgeRetriever", "build_llm_port"]
