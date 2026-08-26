"""Knowledge ingest: Document → Chunks → optional embed job."""

from sqlalchemy.exc import SQLAlchemyError

from app.ai.rag.service import split_text
from app.api.v1.knowledge.dto import CreateDocumentRequest, DocumentResponse
from app.api.v1.knowledge.mapping import KnowledgeMapper
from app.clients.queue import get_queue
from app.core.errors import AppError, NotFoundError
from app.db.document import DocumentRepository
from app.models.document import DocumentChunk
from app.models.user import User


class KnowledgeService:
    """Upload documents, list/delete them, and enqueue embedding jobs."""

    def __init__(self, documents: DocumentRepository) -> None:
        self.documents = documents

    async def list_documents(self, user: User) -> list[DocumentResponse]:
        try:
            rows = await self.documents.list_for_user(user.id)
        except SQLAlchemyError as exc:
            raise AppError(
                "Could not load documents.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
        return [KnowledgeMapper.to_response(row) for row in rows]

    async def create_document(self, user: User, payload: CreateDocumentRequest) -> DocumentResponse:
        document = KnowledgeMapper.to_entity(user.id, payload)
        try:
            # ---------------------------------------------------------------------------
            # Chunks first — keyword RAG works before embeddings finish.
            # ---------------------------------------------------------------------------
            await self.documents.create(document)
            chunks = [
                DocumentChunk(document_id=document.id, chunk_index=i, content=chunk)
                for i, chunk in enumerate(split_text(payload.content))
            ]
            if not chunks:
                raise AppError(
                    "Document content produced no chunks.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                    fields=[{"field": "content", "message": "Content could not be chunked.", "type": "value_error"}],
                )
            await self.documents.add_chunks(chunks)
            await self.documents.db.commit()
            await self.documents.db.refresh(document)
        except AppError:
            await self.documents.db.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.documents.db.rollback()
            raise AppError(
                "Could not save document.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc

        # ---------------------------------------------------------------------------
        # Embed job optional — ingest still succeeds if queue is down.
        # ---------------------------------------------------------------------------
        queue = get_queue()
        if queue is not None:
            try:
                await queue.enqueue_job("process_document", document.id)
            except Exception:
                pass
        return KnowledgeMapper.to_response(document)

    async def delete_document(self, user: User, document_id: str) -> None:
        try:
            document = await self.documents.get_for_user(document_id, user.id)
        except SQLAlchemyError as exc:
            raise AppError(
                "Could not delete document.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
        if document is None:
            raise NotFoundError("Document not found")
        try:
            await self.documents.delete(document)
            await self.documents.db.commit()
        except SQLAlchemyError as exc:
            await self.documents.db.rollback()
            raise AppError(
                "Could not delete document.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
