"""pgvector cosine-distance search over document chunks."""

from app.infrastructure.database.models import Document, DocumentChunk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def search_similar_chunks(
    db: AsyncSession,
    user_id: str,
    vector: list[float],
    k: int = 4,
    *,
    max_distance: float | None = None,
) -> list[str]:
    """Return top-k chunk texts for one user, ordered by cosine distance."""
    distance = DocumentChunk.embedding.cosine_distance(vector)
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .where(DocumentChunk.embedding.is_not(None))
    )
    if max_distance is not None:
        stmt = stmt.where(distance <= max_distance)
    stmt = stmt.order_by(distance).limit(k)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)
