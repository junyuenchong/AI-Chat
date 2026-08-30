"""
LangChain wiring.

Connects llm.py, retrieval.py, and agent.py to the application layer.
Called by core/dependencies.py to build the chat engine for ChatService.
"""

from app.infrastructure.ai.langchain import (
    ChatAgent,
    KnowledgeRetriever,
    build_llm_port,
)


# ────────────────────────────────────────────────────────
# build_chat_engine
# Internal — infrastructure / ai
# Creates the ChatAgent used by ChatService via Depends(get_chat_service).
# ────────────────────────────────────────────────────────
def build_chat_engine() -> ChatAgent:
    """Wire LLM port and retriever into a single ChatAgent."""
    # Step 1: build LLM from settings (or demo mode).
    # Step 2: build retriever for RAG document search.
    return ChatAgent(build_llm_port(), KnowledgeRetriever())
