"""
Map domain chat messages to LangChain message objects.

Request path:
  infrastructure/ai/langchain/llm/provider.py
    → infrastructure/ai/langchain/llm/messages.py  (this file)
    → langchain_core.messages
"""

from collections.abc import Callable

from app.domain.chat.entities import ChatMessage
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

_ROLE_TO_LC: dict[str, Callable[[str], BaseMessage]] = {
    "system": SystemMessage,
    "assistant": AIMessage,
    "user": HumanMessage,
}


# ────────────────────────────────────────────────────────
# to_lc_messages
# Path: infrastructure/ai/langchain/llm/messages.py
# Internal — called before every astream / ainvoke call.
# Use: convert domain ChatMessage dicts to LangChain BaseMessage list.
# ────────────────────────────────────────────────────────
def to_lc_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    """Convert ChatMessage dicts to LangChain BaseMessage list."""
    lc: list[BaseMessage] = []
    for msg in messages:
        role, content = msg["role"], msg["content"]
        # Step 1 — map known roles to the matching LangChain message class.
        if role in _ROLE_TO_LC:
            lc.append(_ROLE_TO_LC[role](content))
        else:
            # Step 2 — unknown roles default to HumanMessage.
            lc.append(HumanMessage(content))
    return lc


# ────────────────────────────────────────────────────────
# parse_stream_chunk
# Path: infrastructure/ai/langchain/llm/messages.py
# Internal — called for each chunk in LangChainLLM.stream().
# Use: normalize string or multi-part chunk content into plain text.
# ────────────────────────────────────────────────────────
def parse_stream_chunk(content: object) -> str:
    """Parse one stream chunk into a text string."""
    # Step 1 — plain string chunk.
    if isinstance(content, str):
        return content
    # Step 2 — list of parts (Gemini multi-part responses).
    if isinstance(content, list):
        return "".join(_parse_chunk_part(part) for part in content)
    return ""


# ────────────────────────────────────────────────────────
# _parse_chunk_part
# Path: infrastructure/ai/langchain/llm/messages.py
# Internal — helper for parse_stream_chunk().
# Use: extract text from one element of a multi-part stream chunk.
# ────────────────────────────────────────────────────────
def _parse_chunk_part(part: object) -> str:
    """Parse one part of a multi-part stream chunk."""
    if isinstance(part, str):
        return part
    if isinstance(part, dict) and part.get("type") == "text":
        return str(part.get("text", ""))
    return ""
