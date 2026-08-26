"""pgvector similarity search over document_chunks."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk


async def search_similar_chunks(
    db: AsyncSession,
    user_id: str,
    vector: list[float],
    k: int = 4,
) -> list[str]:
    """Return top-k chunk texts by cosine distance for this user only."""
    # ---------------------------------------------------------------------------
    # Scope by user_id — never search another user's Knowledge.
    # ---------------------------------------------------------------------------
    stmt = (
        select(DocumentChunk.content)
        .join(Document)
        .where(Document.user_id == user_id)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(DocumentChunk.embedding.cosine_distance(vector))
        .limit(k)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)
