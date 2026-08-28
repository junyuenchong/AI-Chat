"""
Chat prompts.

System prompt text and helpers for adding knowledge-base context.
"""

SYSTEM_PROMPT = """You are a production AI chat assistant for a FastAPI portfolio stack.

Layers:
- LangChain = AI components (prompts, LLM, embeddings, RAG retrieval)
- RAG = Retriever finds Knowledge chunks, then the LLM answers with that context

Be concise, accurate, and practical. If RAG context is provided, prefer it.
If the user asks about this project, explain Conversation vs Knowledge and RAG.
"""

STRICT_RAG_EMPTY_REPLY = (
    "I don't have relevant information in the knowledge base to answer that question."
)

SUMMARIZE_SYSTEM_PROMPT = "You write short conversation summaries for a chat database."

SUMMARIZE_USER_PROMPT = (
    "Summarize this chat in 2-4 sentences. "
    "Keep user intent, decisions, and any follow-ups.\n\n{transcript}"
)


# ────────────────────────────────────────────────────────
# append_rag_context
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Adds retrieved knowledge-base text to the system prompt when available.
# ────────────────────────────────────────────────────────
def append_rag_context(system_prompt: str, rag_context: str | None) -> str:
    """Append knowledge-base search results so the AI can cite uploaded documents."""
    # Leave the base prompt unchanged when no documents matched.
    if not rag_context:
        return system_prompt
    # Append retrieved chunks so the model can ground its answer.
    return f"{system_prompt}\n\nRetrieved context:\n{rag_context}"
