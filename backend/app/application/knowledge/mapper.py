"""
Knowledge mapper.

Converts document upload requests and database rows into API JSON responses.
"""

from app.api.v1.knowledge.dto.request import CreateDocumentRequest
from app.api.v1.knowledge.dto.response import DocumentResponse
from app.infrastructure.database.models.document import Document


class KnowledgeMapper:
    """Convert knowledge document data between HTTP, database, and API layers."""

    # ────────────────────────────────────────────────────────
    # upload_request_to_document
    # Endpoint: POST /documents (internal)
    # Turns upload form fields into a Document row ready to save.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def upload_request_to_document(
        user_id: str, request: CreateDocumentRequest
    ) -> Document:
        """Build a new Document owned by the logged-in user."""
        # Create a document row tied to the uploading user.
        return Document(
            user_id=user_id,
            filename=request.filename,
            content=request.content,
        )

    # ────────────────────────────────────────────────────────
    # document_to_list_item
    # Endpoint: GET /documents, POST /documents (internal)
    # Returns filename and dates only — not the full document text.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def document_to_list_item(document: Document) -> DocumentResponse:
        """Return document metadata for list and upload responses."""
        # Expose metadata only — full text stays server-side for RAG.
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            created_at=document.created_at,
        )
