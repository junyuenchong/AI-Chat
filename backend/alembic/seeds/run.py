"""
Seed runner.

Usage:
  python alembic/seeds/run.py
  python alembic/seeds/run.py --embed

Docker:
  docker compose run --rm api python alembic/seeds/run.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SEEDS_DIR.parents[1]

sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(SEEDS_DIR))

from app.infrastructure.database.models import load_models  # noqa: E402
from app.infrastructure.database.session import SessionLocal, init_db  # noqa: E402
from documents import seed_documents  # noqa: E402
from users import (  # noqa: E402
    DEMO_USER_EMAIL,
    DEMO_USER_PASSWORD,
    seed_conversations,
    seed_users,
)


@dataclass(frozen=True)
class SeedResult:
    """Summary returned after a seed run."""

    user_created: bool
    documents_created: int
    conversation_created: bool
    embeddings_processed: int


# ────────────────────────────────────────────────────────
# seed_database
# CLI: python alembic/seeds/run.py
# Bootstraps demo data for interviews and local development.
# ────────────────────────────────────────────────────────
async def seed_database(*, embed: bool = False) -> SeedResult:
    """Seed reference data. Skips rows that already exist."""
    load_models()
    await init_db()

    async with SessionLocal() as db:
        user, user_created = await seed_users(db)
        documents_created, embeddings_processed = await seed_documents(
            db,
            user.id,
            embed=embed,
        )
        conversation_created = await seed_conversations(db, user.id)
        await db.commit()

    return SeedResult(
        user_created=user_created,
        documents_created=documents_created,
        conversation_created=conversation_created,
        embeddings_processed=embeddings_processed,
    )


# ────────────────────────────────────────────────────────
# main
# CLI entrypoint for reference data seeding.
# ────────────────────────────────────────────────────────
async def _run(embed: bool) -> None:
    """Run all seed modules and print a short summary."""
    result = await seed_database(embed=embed)

    print("Seed complete.")
    print(f"  user_created: {result.user_created}")
    print(f"  documents_created: {result.documents_created}")
    print(f"  conversation_created: {result.conversation_created}")
    print(f"  embeddings_processed_chunks: {result.embeddings_processed}")
    print()
    print("Demo login:")
    print(f"  email: {DEMO_USER_EMAIL}")
    print(f"  password: {DEMO_USER_PASSWORD}")


def main() -> None:
    """Parse CLI flags and seed the database."""
    parser = argparse.ArgumentParser(description="Seed demo users and documents.")
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Embed document chunks inline (requires LLM API key).",
    )
    args = parser.parse_args()
    asyncio.run(_run(embed=args.embed))


if __name__ == "__main__":
    main()
