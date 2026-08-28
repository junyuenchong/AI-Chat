"""Performance indexes — conversation history, document chunks, updated_at sort."""

from collections.abc import Sequence

from alembic import op

revision: str = "002_perf_indexes"
down_revision: str | Sequence[str] | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
    )
    op.create_index(
        "ix_conversations_user_updated",
        "conversations",
        ["user_id", "updated_at"],
    )
    op.create_index(
        "ix_document_chunks_doc_index",
        "document_chunks",
        ["document_id", "chunk_index"],
    )
    op.create_index(
        "ix_documents_user_created",
        "documents",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_documents_user_created", table_name="documents")
    op.drop_index("ix_document_chunks_doc_index", table_name="document_chunks")
    op.drop_index("ix_conversations_user_updated", table_name="conversations")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
