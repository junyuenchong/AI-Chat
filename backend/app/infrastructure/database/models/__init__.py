"""
ORM models package.

Call load_models() before create_all.
"""

from app.infrastructure.database.models.base import Base


# ────────────────────────────────────────────────────────
# load_models
# Internal — database
# Imports all ORM modules so metadata is registered before create_all.
# ────────────────────────────────────────────────────────
def load_models() -> None:
    # Side-effect imports register every table on Base.metadata.
    from app.infrastructure.database.models import (  # noqa: F401
        conversation,
        document,
        message,
        user,
    )


__all__ = ["Base", "load_models"]
