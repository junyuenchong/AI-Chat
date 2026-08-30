"""Shared pytest fixtures and test environment setup."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

_TEST_JWT_SECRET = "test-jwt-secret-key-min-32-bytes-long!!"
os.environ["JWT_SECRET_KEY"] = _TEST_JWT_SECRET
# Deterministic chat tests — never call external LLM APIs during pytest.
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_FALLBACK_MODEL"] = ""

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from tests.helpers import auth_headers, register_user

_services_ready = False


@pytest.fixture(autouse=True)
def _test_settings() -> Iterator[None]:
    os.environ["JWT_SECRET_KEY"] = _TEST_JWT_SECRET
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["GEMINI_FALLBACK_MODEL"] = ""
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    yield
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def pytest_configure(config) -> None:
    os.environ["JWT_SECRET_KEY"] = _TEST_JWT_SECRET
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["GEMINI_FALLBACK_MODEL"] = ""


def pytest_collection_modifyitems(config, items) -> None:
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
        else:
            item.add_marker(pytest.mark.unit)


async def _ensure_services() -> None:
    global _services_ready
    if _services_ready:
        return

    from app.infrastructure.database.session import engine, init_db

    last_error: Exception | None = None
    for _ in range(10):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            break
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.3)
    else:
        pytest.skip(
            f"Postgres not available — run: docker compose up -d ({last_error})"
        )

    await init_db()
    _services_ready = True


@pytest.fixture
async def api_client() -> AsyncIterator[AsyncClient]:
    from app.core.config import get_settings

    get_settings.cache_clear()
    await _ensure_services()
    from app.main import create_app

    application = create_app()
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def live_client(
    api_client: AsyncClient,
) -> AsyncIterator[AsyncClient | httpx.AsyncClient]:
    external = os.getenv("E2E_BASE_URL", "").rstrip("/")
    if external:
        async with httpx.AsyncClient(base_url=external, timeout=60.0) as client:
            yield client
    else:
        yield api_client


@pytest.fixture
async def auth_user(api_client: AsyncClient) -> dict[str, Any]:
    from uuid import uuid4

    registered = await register_user(
        api_client, email=f"user-{uuid4().hex}@example.com"
    )
    return {
        **registered,
        "headers": auth_headers(registered["access_token"]),
    }
