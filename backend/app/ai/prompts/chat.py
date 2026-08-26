"""Chat system prompts — product copy lives here, not in services."""

SYSTEM_PROMPT = """You are a production AI chat assistant for a FastAPI portfolio stack.

Layers:
- LangChain = AI components (prompts, LLM, embeddings, RAG retrieval)
- RAG = Retriever finds Knowledge chunks, then the LLM answers with that context

Be concise, accurate, and practical. If RAG context is provided, prefer it.
If the user asks about this project, explain Conversation vs Knowledge and RAG.
"""


# ---------------------------------------------------------------------------
# Append retrieved chunks so the LLM prefers Knowledge over generic answers.
# ---------------------------------------------------------------------------
def with_rag_context(system_prompt: str, rag_context: str | None) -> str:
    if not rag_context:
        return system_prompt
    return f"{system_prompt}\n\nRetrieved context:\n{rag_context}"
