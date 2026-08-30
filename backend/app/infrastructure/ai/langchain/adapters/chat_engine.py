"""
Wire LangChain adapters into domain ports.

Request path:
  core/dependencies.py (get_chat_engine)
    → infrastructure/ai/langchain/adapters/chat_engine.py  (this file)
    → infrastructure/ai/langchain/chains/chat_chain.py
"""

from app.infrastructure.ai.langchain.chains import ChatChain
from app.infrastructure.ai.langchain.llm import build_llm_port


# ────────────────────────────────────────────────────────
# build_chat_engine
# Path: infrastructure/ai/langchain/adapters/chat_engine.py
# Internal — called by core/dependencies.py at startup.
# Use: wire the LLM port into ChatChain for ChatService injection.
# ────────────────────────────────────────────────────────
def build_chat_engine() -> ChatChain:
    """Wire the LLM port into the Q2 chat chain."""
    # Step 1 — build DemoLLM or LangChainLLM from Settings.
    llm = build_llm_port()
    # Step 2 — return ChatChain as the domain ChatEngine implementation.
    return ChatChain(llm)
