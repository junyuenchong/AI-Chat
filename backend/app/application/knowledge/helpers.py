"""
Knowledge application helpers.

Splits uploaded text into chunks and schedules background embedding jobs.
"""

from app.core.exceptions import AppException
from app.infrastructure.database.models.document import DocumentChunk
from app.infrastructure.queue.queue import get_queue
from app.infrastructure.vectorstore.retriever import split_text


# ────────────────────────────────────────────────────────
# split_document_into_chunks
# Endpoint: POST /documents (internal)
# Breaks uploaded text into smaller pieces for search and embedding.
# ────────────────────────────────────────────────────────
def split_document_into_chunks(document_id: str, content: str) -> list[DocumentChunk]:
    """Split document text into numbered chunks stored in the database."""
    # Turn each text segment into a numbered chunk row.
    chunks = [
        DocumentChunk(document_id=document_id, chunk_index=i, content=chunk)
        for i, chunk in enumerate(split_text(content))
    ]
    if not chunks:
        # Reject uploads that produce no searchable text.
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
# schedule_embedding_job
# Endpoint: POST /documents (internal)
# Queues a background job to create vector embeddings after upload.
# ────────────────────────────────────────────────────────
async def schedule_embedding_job(document_id: str) -> None:
    """Add document to the embedding queue. Does nothing if no worker is running."""
    # Skip queueing when no background worker is configured.
    queue = get_queue()
    if queue is None:
        return
    try:
        # Enqueue embedding so vectors are built after the upload response.
        await queue.enqueue_job("process_document", document_id)
    except Exception:
        pass  # Upload already succeeded — embedding can be retried later.
