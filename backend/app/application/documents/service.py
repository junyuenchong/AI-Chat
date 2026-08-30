"""
Documents application service.

Uploads, lists, and deletes knowledge-base documents used for RAG search.
"""

from app.core.exceptions import (
    AppException,
    DocumentNotFound,
    database_error,
    require_found,
)
from app.domain.document.entities import DocumentUpload
from app.infrastructure.ai.langchain.retrieval import split_text
from app.infrastructure.database.models import Document, DocumentChunk, User
from app.infrastructure.database.repositories.document import DocumentRepository
from app.infrastructure.messaging.queue import get_queue
from sqlalchemy.exc import SQLAlchemyError


# ────────────────────────────────────────────────────────
# _split_document_into_chunks
# Endpoint: POST /documents (internal)
# Breaks uploaded text into smaller pieces for search and embedding.
# ────────────────────────────────────────────────────────
def _split_document_into_chunks(document_id: str, content: str) -> list[DocumentChunk]:
    """Split document text into numbered chunks stored in the database."""
    chunks = [
        DocumentChunk(document_id=document_id, chunk_index=i, content=chunk)
        for i, chunk in enumerate(split_text(content))
    ]
    if not chunks:
        raise AppException(
            "Document content produced no chunks.",
            code="VALIDATION_ERROR",
            status_code=422,
            fields=[
                {
                    "field": "content",
                    "message": "Content could not be chunked.",
                    "type": "value_error",
                }
            ],
        )
    return chunks


# ────────────────────────────────────────────────────────
# _schedule_embedding_job
# Endpoint: POST /documents (internal)
# Queues a background job to create vector embeddings after upload.
# ────────────────────────────────────────────────────────
async def _schedule_embedding_job(document_id: str) -> None:
    """Add document to the embedding queue. Does nothing if no worker is running."""
    queue = get_queue()
    if queue is None:
        return
    try:
        await queue.enqueue_job("process_document", document_id)
    except Exception:
        pass


class DocumentsService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Stores the document repository for database access.
    # ────────────────────────────────────────────────────────
    def __init__(self, documents: DocumentRepository) -> None:
        """Receive the document repository from FastAPI dependencies."""
        self.documents = documents

    # ────────────────────────────────────────────────────────
    # list_documents
    # Endpoint: GET /documents
    # Returns all uploaded documents for the knowledge page.
    # ────────────────────────────────────────────────────────
    async def list_documents(self, user: User) -> list[Document]:
        """Load every document owned by this user."""
        try:
            return await self.documents.list_for_user(user.id)
        except SQLAlchemyError as exc:
            raise database_error("Could not load documents.", exc) from exc

    # ────────────────────────────────────────────────────────
    # create_document
    # Endpoint: POST /documents
    # Saves uploaded text, splits it into chunks, and queues embedding.
    # ────────────────────────────────────────────────────────
    async def create_document(self, user: User, upload: DocumentUpload) -> Document:
        """Upload a document: save to DB, chunk text, schedule vector embedding."""
        document = Document(
            user_id=upload.user_id,
            filename=upload.filename,
            content=upload.content,
        )

        try:
            await self.documents.create(document)
            chunks = _split_document_into_chunks(document.id, upload.content)
            await self.documents.add_chunks(chunks)
            await self.documents.db.commit()
            await self.documents.db.refresh(document)
        except AppException:
            await self.documents.db.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.documents.db.rollback()
            raise database_error("Could not save document.", exc) from exc

        # Runs in background — response returns immediately.
        await _schedule_embedding_job(document.id)
        return document

    # ────────────────────────────────────────────────────────
    # delete_document
    # Endpoint: DELETE /documents/{document_id}
    # Removes a document and its search index chunks.
    # ────────────────────────────────────────────────────────
    async def delete_document(self, user: User, document_id: str) -> None:
        """Delete one document and all of its text chunks."""
        try:
            document = await self.documents.get_for_user(document_id, user.id)
        except SQLAlchemyError as exc:
            raise database_error("Could not delete document.", exc) from exc
        document = require_found(document, exc=DocumentNotFound)

        try:
            await self.documents.delete(document)
            await self.documents.db.commit()
        except SQLAlchemyError as exc:
            await self.documents.db.rollback()
            raise database_error("Could not delete document.", exc) from exc
