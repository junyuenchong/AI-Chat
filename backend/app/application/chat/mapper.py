"""
Chat mapper.

Converts between API DTOs, application commands, and response DTOs.
"""

from app.api.v1.chat.dto.request import ChatRequest
from app.api.v1.chat.dto.response import ChatCompleteResponse
from app.application.chat.commands import ChatCommand, ChatCompleteResult


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
        return ChatCommand(
            user_id=user_id,
            message=request.message.strip(),
            conversation_id=str(request.conversation_id)
            if request.conversation_id
            else None,
        )

    # ────────────────────────────────────────────────────────
    # complete_result_to_response
    # Endpoint: POST /chat/complete (internal)
    # Wraps the application result into the JSON shape the client expects.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def complete_result_to_response(result: ChatCompleteResult) -> ChatCompleteResponse:
        """Build the non-streaming chat response with conversation id and reply text."""
        return ChatCompleteResponse(
            conversation_id=result.conversation_id,
            content=result.content,
            llm=result.llm,
        )
