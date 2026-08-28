"""Map domain chat messages to LangChain message objects."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.domain.chat.entities import ChatMessage

_ROLE_TO_LC: dict[str, Callable[[str], BaseMessage]] = {
    "system": SystemMessage,
    "assistant": AIMessage,
    "user": HumanMessage,
}


def to_lc_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    lc: list[BaseMessage] = []
    for msg in messages:
        role, content = msg["role"], msg["content"]
        if role in _ROLE_TO_LC:
            lc.append(_ROLE_TO_LC[role](content))
        else:
            lc.append(HumanMessage(content))
    return lc
