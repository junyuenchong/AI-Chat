"""Conversation persistence port."""

from typing import Any, Protocol


class ConversationRepositoryPort(Protocol):
    async def list_for_user(self, user_id: str, *, limit: int = 100) -> list[Any]: ...

    async def get_for_user(self, conversation_id: str, user_id: str) -> Any | None: ...

    async def get_with_messages(
        self, conversation_id: str, user_id: str
    ) -> Any | None: ...

    async def create(self, conversation: Any) -> Any: ...

    async def delete(self, conversation: Any) -> None: ...
