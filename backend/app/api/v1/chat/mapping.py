"""Chat response mapping."""

from app.api.v1.chat.dto import ChatCompleteResponse


class ChatMapper:
    """Build chat response DTOs from service results."""

    @staticmethod
    def to_complete_response(conversation_id: str, content: str, llm: str) -> ChatCompleteResponse:
        return ChatCompleteResponse(
            conversation_id=conversation_id,
            content=content,
            llm=llm,
        )
