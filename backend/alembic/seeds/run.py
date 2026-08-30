"""
Seed runner.

Usage:
  python alembic/seeds/run.py

Docker:
  docker compose run --rm api python alembic/seeds/run.py
"""

from __future__ import annotations

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
from users import (  # noqa: E402
    DEMO_USER_EMAIL,
    DEMO_USER_PASSWORD,
    seed_conversations,
    seed_users,
)


@dataclass(frozen=True)
class SeedResult:
    user_created: bool
    conversation_created: bool


async def seed_database() -> SeedResult:
    load_models()
    await init_db()

    async with SessionLocal() as db:
        user, user_created = await seed_users(db)
        conversation_created = await seed_conversations(db, user.id)
        await db.commit()

    return SeedResult(
        user_created=user_created,
        conversation_created=conversation_created,
    )


async def _run() -> None:
    result = await seed_database()
    print("Seed complete.")
    print(f"  user_created: {result.user_created}")
    print(f"  conversation_created: {result.conversation_created}")
    print()
    print("Demo login:")
    print(f"  email: {DEMO_USER_EMAIL}")
    print(f"  password: {DEMO_USER_PASSWORD}")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
