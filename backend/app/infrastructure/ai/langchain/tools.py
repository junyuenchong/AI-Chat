"""
LangChain tools.

Callable capabilities the AI can use (search, APIs, calculators, etc.).
Register tools in TOOLS — agent.py uses this list when tool-calling is enabled.
"""

from app.infrastructure.ai.langchain.retrieval import KnowledgeRetriever
from langchain_core.tools import tool

_retriever = KnowledgeRetriever()


# ────────────────────────────────────────────────────────
# search_knowledge
# Internal — langchain / tools
# Search the user's uploaded documents for relevant context.
# ────────────────────────────────────────────────────────
@tool
async def search_knowledge(user_id: str, query: str) -> str:
    """Search the user's uploaded documents for relevant context."""
    # Delegate to retrieval.py (embed → vector search → context).
    result = await _retriever.retrieve(user_id, query)
    # Return context text or a clear not-found message.
    return result or "No matching documents found."


# Register all tools here. agent.py will use this list when tool-calling is wired up.
TOOLS = [search_knowledge]
