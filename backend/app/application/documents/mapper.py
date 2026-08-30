"""
Documents mapper.

Converts document upload requests and database rows into API JSON responses.
"""

from app.api.v1.documents.dto.request import CreateDocumentRequest
from app.api.v1.documents.dto.response import DocumentResponse
from app.domain.document.entities import DocumentUpload
from app.infrastructure.database.models import Document


class DocumentsMapper:
    """Convert document data between HTTP, application, and database layers."""

    # ────────────────────────────────────────────────────────
    # request_to_upload
    # Endpoint: POST /documents (internal)
    # Turns upload form fields into a validated application input object.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def request_to_upload(
        user_id: str, request: CreateDocumentRequest
    ) -> DocumentUpload:
        """Build a DocumentUpload from the HTTP request body."""
        return DocumentUpload(
            user_id=user_id,
            filename=request.filename,
            content=request.content,
        )

    # ────────────────────────────────────────────────────────
    # upload_to_document
    # Endpoint: POST /documents (internal)
    # Converts application input into a Document ORM row ready to save.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def upload_to_document(upload: DocumentUpload) -> Document:
        """Build a new Document owned by the logged-in user."""
        return Document(
            user_id=upload.user_id,
            filename=upload.filename,
            content=upload.content,
        )

    # ────────────────────────────────────────────────────────
    # document_to_response
    # Endpoint: GET /documents, POST /documents (internal)
    # Returns filename and dates only — not the full document text.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def document_to_response(document: Document) -> DocumentResponse:
        """Return document metadata for list and upload responses."""
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            created_at=document.created_at,
        )
