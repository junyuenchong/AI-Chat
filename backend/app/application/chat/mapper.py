"""
Chat mapper.

Converts chat HTTP requests and service results into commands and JSON responses.
"""

from app.api.v1.chat.dto.request import ChatRequest
from app.api.v1.chat.dto.response import ChatCompleteResponse
from app.application.chat.commands import ChatCommand


class ChatMapper:
    """Convert chat data between HTTP layer and application layer."""

    # ────────────────────────────────────────────────────────
    # request_to_command
    # Endpoint: POST /chat/stream, POST /chat/complete (internal)
    # Turns the HTTP chat body plus user id into a ChatCommand object.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def request_to_command(request: ChatRequest, user_id: str) -> ChatCommand:
        """Normalize the incoming chat request for the service layer."""
        # Package HTTP fields into a command the chat service understands.
        return ChatCommand(
            user_id=user_id,
            message=request.message.strip(),
            conversation_id=str(request.conversation_id)
            if request.conversation_id
            else None,
            use_rag=request.use_rag,
        )

    # ────────────────────────────────────────────────────────
    # reply_to_response
    # Endpoint: POST /chat/complete (internal)
    # Wraps the AI reply into the JSON shape the client expects.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def reply_to_response(
        conversation_id: str, content: str, llm: str
    ) -> ChatCompleteResponse:
        """Build the non-streaming chat response with conversation id and reply text."""
        # Shape the final reply into the API response DTO.
        return ChatCompleteResponse(
            conversation_id=conversation_id,
            content=content,
            llm=llm,
        )
