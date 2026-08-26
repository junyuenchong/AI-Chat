"""Document persistence including chunk replace for the ARQ embed job."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk


class DocumentRepository:
    """Persist documents and replace chunks after embed jobs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(self, user_id: str) -> list[Document]:
        rows = await self.db.scalars(
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        return list(rows.all())

    async def get_for_user(self, document_id: str, user_id: str) -> Document | None:
        return await self.db.scalar(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )

    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        return document

    async def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)

    # ---------------------------------------------------------------------------
    # Replace — delete then insert so re-embed jobs stay idempotent.
    # ---------------------------------------------------------------------------
    async def replace_chunks(self, document_id: str, chunks: list[DocumentChunk]) -> None:
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        self.db.add_all(chunks)

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
