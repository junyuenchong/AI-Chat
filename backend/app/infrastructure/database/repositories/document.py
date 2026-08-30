"""
Document repository.

Persistence for documents and chunk replace after embed jobs.
"""

from app.infrastructure.database.models import Document, DocumentChunk
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository:
    """Persist documents and replace chunks after embed jobs."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — database
    # Stores the async SQLAlchemy session for repository queries.
    # ────────────────────────────────────────────────────────
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ────────────────────────────────────────────────────────
    # list_for_user
    # Internal — database
    # Returns recent documents owned by the given user.
    # ────────────────────────────────────────────────────────
    async def list_for_user(self, user_id: str, *, limit: int = 200) -> list[Document]:
        # Newest uploads first, capped at the caller's limit.
        rows = await self.db.scalars(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        return list(rows.all())

    # ────────────────────────────────────────────────────────
    # get_for_user
    # Internal — database
    # Loads one document scoped to the owning user.
    # ────────────────────────────────────────────────────────
    async def get_for_user(self, document_id: str, user_id: str) -> Document | None:
        # Scope lookup to the owning user to prevent cross-tenant access.
        return await self.db.scalar(
            select(Document).where(
                Document.id == document_id, Document.user_id == user_id
            )
        )

    # ────────────────────────────────────────────────────────
    # create
    # Internal — database
    # Persists a new document row and returns the flushed entity.
    # ────────────────────────────────────────────────────────
    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        return document

    # ────────────────────────────────────────────────────────
    # add_chunks
    # Internal — database
    # Inserts document chunks without replacing existing rows.
    # ────────────────────────────────────────────────────────
    async def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)

    # ────────────────────────────────────────────────────────
    # replace_chunks
    # Internal — database
    # Replaces all chunks for a document so embed jobs stay idempotent.
    # ────────────────────────────────────────────────────────
    async def replace_chunks(
        self, document_id: str, chunks: list[DocumentChunk]
    ) -> None:
        """Delete then insert so re-embed jobs stay idempotent."""
        # Remove stale chunks before inserting the new set.
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        self.db.add_all(chunks)

    # ────────────────────────────────────────────────────────
    # delete
    # Internal — database
    # Deletes a document and its related chunks via ORM cascade.
    # ────────────────────────────────────────────────────────
    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
