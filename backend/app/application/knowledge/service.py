"""
Knowledge application service.

Uploads, lists, and deletes knowledge-base documents used for RAG search.
"""

from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.knowledge.dto.request import CreateDocumentRequest
from app.api.v1.knowledge.dto.response import DocumentResponse
from app.application.knowledge.helpers import (
    schedule_embedding_job,
    split_document_into_chunks,
)
from app.application.knowledge.mapper import KnowledgeMapper
from app.core.exceptions import (
    AppException,
    DocumentNotFound,
    database_error,
    require_found,
)
from app.infrastructure.database.models.user import User
from app.infrastructure.database.repositories.document_repository import (
    DocumentRepository,
)


class KnowledgeService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Stores the document repository for database access.
    # ────────────────────────────────────────────────────────
    def __init__(self, documents: DocumentRepository) -> None:
        """Receive the document repository from FastAPI dependencies."""
        # Keep the repository on the service for all document operations.
        self.documents = documents

    # ────────────────────────────────────────────────────────
    # list_documents
    # Endpoint: GET /documents
    # Returns all uploaded documents for the knowledge page.
    # ────────────────────────────────────────────────────────
    async def list_documents(self, user: User) -> list[DocumentResponse]:
        """Load every document owned by this user."""
        try:
            # Fetch all documents belonging to the logged-in user.
            rows = await self.documents.list_for_user(user.id)
        except SQLAlchemyError as exc:
            raise database_error("Could not load documents.", exc) from exc

        # Map each row to the list response shape (no full text).
        return [KnowledgeMapper.document_to_list_item(row) for row in rows]

    # ────────────────────────────────────────────────────────
    # create_document
    # Endpoint: POST /documents
    # Saves uploaded text, splits it into chunks, and queues embedding.
    # ────────────────────────────────────────────────────────
    async def create_document(
        self, user: User, payload: CreateDocumentRequest
    ) -> DocumentResponse:
        """Upload a document: save to DB, chunk text, schedule vector embedding."""
        # Build a document row from the upload request.
        document = KnowledgeMapper.upload_request_to_document(user.id, payload)

        try:
            # Save the document, split it into chunks, and commit.
            await self.documents.create(document)
            chunks = split_document_into_chunks(document.id, payload.content)
            await self.documents.add_chunks(chunks)
            await self.documents.db.commit()
            # Refresh so generated fields (like id/timestamps) are loaded.
            await self.documents.db.refresh(document)
        except AppException:
            # Re-raise validation errors after rolling back.
            await self.documents.db.rollback()
            raise
        except SQLAlchemyError as exc:
            # Wrap database failures in a consistent error type.
            await self.documents.db.rollback()
            raise database_error("Could not save document.", exc) from exc

        await schedule_embedding_job(
            document.id
        )  # Runs in background — response returns immediately.
        # Return metadata for the newly created document.
        return KnowledgeMapper.document_to_list_item(document)

    # ────────────────────────────────────────────────────────
    # delete_document
    # Endpoint: DELETE /documents/{document_id}
    # Removes a document and its search index chunks.
    # ────────────────────────────────────────────────────────
    async def delete_document(self, user: User, document_id: str) -> None:
        """Delete one document and all of its text chunks."""
        try:
            # Verify the document exists and belongs to this user.
            document = await self.documents.get_for_user(document_id, user.id)
        except SQLAlchemyError as exc:
            raise database_error("Could not delete document.", exc) from exc
        document = require_found(document, exc=DocumentNotFound)

        try:
            # Delete the row (cascades to chunks) and commit.
            await self.documents.delete(document)
            await self.documents.db.commit()
        except SQLAlchemyError as exc:
            # Roll back if the delete fails partway through.
            await self.documents.db.rollback()
            raise database_error("Could not delete document.", exc) from exc
