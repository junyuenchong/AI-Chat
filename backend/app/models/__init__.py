"""Database models — call load_models() before create_all so tables register."""

from app.models.base import Base


def load_models() -> None:
    # Side-effect imports register metadata on Base for init_db / Alembic.
    from app.models import conversation as conversation_models  # noqa: F401
    from app.models import document as document_models  # noqa: F401
    from app.models import message as message_models  # noqa: F401
    from app.models import user as user_models  # noqa: F401


__all__ = ["Base", "load_models"]
