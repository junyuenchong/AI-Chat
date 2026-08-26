"""RAG / summarize prompts used by background summarize jobs."""

SUMMARIZE_SYSTEM_PROMPT = "You write short conversation summaries for a chat database."

SUMMARIZE_USER_PROMPT = (
    "Summarize this chat in 2-4 sentences. Keep user intent, decisions, and any follow-ups.\n\n{transcript}"
)
