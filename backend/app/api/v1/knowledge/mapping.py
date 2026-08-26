"""Knowledge entity ↔ DTO — DocumentResponse omits full content on purpose."""

from app.api.v1.knowledge.dto import CreateDocumentRequest, DocumentResponse
from app.models.document import Document


class KnowledgeMapper:
    """Map document request DTOs → Document and Document → response DTOs."""

    @staticmethod
    def to_entity(user_id: str, request: CreateDocumentRequest) -> Document:
        return Document(
            user_id=user_id,
            filename=request.filename,
            content=request.content,
        )

    # ---------------------------------------------------------------------------
    # List/create — metadata only so large text never dumps into list responses.
    # ---------------------------------------------------------------------------
    @staticmethod
    def to_response(document: Document) -> DocumentResponse:
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            created_at=document.created_at,
        )
