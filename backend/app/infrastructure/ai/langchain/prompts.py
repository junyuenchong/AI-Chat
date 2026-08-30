"""
Prompt templates.

HTTP-agnostic text that tells the AI how to answer.
Used by agent.py before every LLM call.
"""

# ────────────────────────────────────────────────────────
# SYSTEM_PROMPT
# Internal — langchain / prompts
# Base instructions sent with every chat message.
# ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a production AI chat assistant for a FastAPI portfolio stack.

Layers:
- LangChain = AI components (prompts, LLM, embeddings, RAG retrieval)
- RAG = Retriever finds Knowledge chunks, then the LLM answers with that context

Be concise, accurate, and practical. If RAG context is provided, prefer it.
If the user asks about this project, explain Conversation vs Knowledge and RAG.
"""

# ────────────────────────────────────────────────────────
# STRICT_RAG_EMPTY_REPLY
# Internal — langchain / prompts
# Returned when RAG is required but no documents matched (strict mode).
# ────────────────────────────────────────────────────────
STRICT_RAG_EMPTY_REPLY = (
    "I don't have relevant information in the knowledge base to answer that question."
)

# ────────────────────────────────────────────────────────
# SUMMARIZE_SYSTEM_PROMPT
# Internal — langchain / prompts
# System role for the background summarize job.
# ────────────────────────────────────────────────────────
SUMMARIZE_SYSTEM_PROMPT = "You write short conversation summaries for a chat database."

# ────────────────────────────────────────────────────────
# SUMMARIZE_USER_PROMPT
# Internal — langchain / prompts
# User role for summarize — {transcript} is filled at runtime.
# ────────────────────────────────────────────────────────
SUMMARIZE_USER_PROMPT = (
    "Summarize this chat in 2-4 sentences. "
    "Keep user intent, decisions, and any follow-ups.\n\n{transcript}"
)


# ────────────────────────────────────────────────────────
# append_rag_context
# Internal — langchain / prompts
# Injects retrieved document text into the system prompt.
# ────────────────────────────────────────────────────────
def append_rag_context(system_prompt: str, rag_context: str | None) -> str:
    """Append RAG context under 'Retrieved context:' or return the base prompt."""
    # No RAG hits — keep the original system instructions.
    if not rag_context:
        return system_prompt
    # Add retrieved chunks so the LLM can ground its answer.
    return f"{system_prompt}\n\nRetrieved context:\n{rag_context}"
