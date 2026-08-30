"""
Document seeds.

Loads sample knowledge-base files used in RAG demos.
"""

from __future__ import annotations

from app.infrastructure.ai.langchain.retrieval import split_text
from app.infrastructure.database.models import Document, DocumentChunk
from app.infrastructure.database.repositories.document import DocumentRepository
from app.infrastructure.messaging.tasks.document import process_document
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DEMO_DOCUMENTS: tuple[tuple[str, str], ...] = (
    (
        "hr-policy.md",
        (
            "# HR Policy\n\n"
            "Annual leave: 14 days per calendar year for full-time employees.\n"
            "Sick leave: 10 days per year.\n"
            "Remote work: up to 2 days per week with manager approval.\n"
        ),
    ),
    (
        "onboarding.md",
        (
            "# Onboarding\n\n"
            "Day 1: IT setup, security training, and team introduction.\n"
            "Week 1: shadow a teammate and read the product wiki.\n"
            "Month 1: complete your first small feature or support ticket.\n"
        ),
    ),
)


# ────────────────────────────────────────────────────────
# seed_documents
# Internal — alembic/seeds
# Inserts sample knowledge-base files and optionally embeds their chunks.
# ────────────────────────────────────────────────────────
async def seed_documents(
    db: AsyncSession,
    user_id: str,
    *,
    embed: bool,
) -> tuple[int, int]:
    """Create missing demo documents and optionally embed their chunks."""
    repo = DocumentRepository(db)
    created = 0
    embeddings_processed = 0

    for filename, content in DEMO_DOCUMENTS:
        exists = await db.scalar(
            select(Document.id).where(
                Document.user_id == user_id,
                Document.filename == filename,
            )
        )
        if exists is not None:
            if embed:
                embeddings_processed += await process_document({}, exists)
            continue

        document = Document(user_id=user_id, filename=filename, content=content)
        await repo.create(document)
        chunks = [
            DocumentChunk(document_id=document.id, chunk_index=i, content=chunk)
            for i, chunk in enumerate(split_text(content))
        ]
        await repo.add_chunks(chunks)
        created += 1

        if embed:
            await db.commit()
            embeddings_processed += await process_document({}, document.id)

    return created, embeddings_processed
