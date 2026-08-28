"""Shared pytest fixtures and test environment setup."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any
from unittest.mock import MagicMock

_TEST_JWT_SECRET = "test-jwt-secret-key-min-32-bytes-long!!"
os.environ["JWT_SECRET_KEY"] = _TEST_JWT_SECRET

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from tests.helpers import FakeRedis, auth_headers, patch_get_redis, register_user

_services_ready = False


# ────────────────────────────────────────────────────────────
# _test_settings
# Internal — autouse fixture
# Use: every test uses a valid JWT secret and a fresh settings cache.
# ────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _test_settings() -> Iterator[None]:
    os.environ["JWT_SECRET_KEY"] = _TEST_JWT_SECRET
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


# ────────────────────────────────────────────────────────────
# test_redis
# Internal — autouse fixture
# Use: fresh in-memory Redis per test so rate limits do not leak between tests.
# ────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def test_redis(monkeypatch) -> FakeRedis:
    fake = FakeRedis()
    patch_get_redis(monkeypatch, fake)
    return fake


def pytest_configure(config) -> None:
    os.environ["JWT_SECRET_KEY"] = _TEST_JWT_SECRET


def pytest_collection_modifyitems(config, items) -> None:
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
        else:
            item.add_marker(pytest.mark.unit)


# ────────────────────────────────────────────────────────────
# _ensure_services
# Internal — called by api_client fixture
# Use: connect to Postgres once per session before integration tests run.
# ────────────────────────────────────────────────────────────


async def _ensure_services() -> None:
    global _services_ready
    if _services_ready:
        return

    from app.core.database import engine, init_db
    from app.infrastructure.cache.redis import init_redis

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
    try:
        await init_redis()
    except Exception:
        pass
    _services_ready = True


# ────────────────────────────────────────────────────────────
# api_client
# Internal — integration test fixture
# Use: in-process HTTP client wired to the FastAPI app with a real database.
# ────────────────────────────────────────────────────────────


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


# ────────────────────────────────────────────────────────────
# live_client
# Internal — e2e test fixture
# Use: HTTP client for e2e tests — external URL if E2E_BASE_URL is set, else in-process.
# ────────────────────────────────────────────────────────────


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


# ────────────────────────────────────────────────────────────
# auth_user
# Internal — integration test fixture
# Use: registered user with JWT token and headers, isolated per test.
# ────────────────────────────────────────────────────────────


@pytest.fixture
async def auth_user(api_client: AsyncClient) -> dict[str, Any]:
    from uuid import uuid4

    registered = await register_user(
        api_client, email=f"user-{uuid4().hex}@example.com"
    )
    api_client.cookies.clear()
    return {
        **registered,
        "headers": auth_headers(registered["access_token"]),
    }


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


# ────────────────────────────────────────────────────────────
# rate_limit_settings
# Internal — chat rate limit tests
# Use: lower the per-minute chat limit so 429 can be tested quickly.
# ────────────────────────────────────────────────────────────


@pytest.fixture
def rate_limit_settings(monkeypatch) -> Iterator[MagicMock]:
    settings = MagicMock()
    settings.rate_limit_per_minute = 2
    monkeypatch.setattr("app.core.logging.get_settings", lambda: settings)
    return settings


@pytest.fixture
def patch_redis(monkeypatch, fake_redis: FakeRedis) -> FakeRedis:
    patch_get_redis(monkeypatch, fake_redis)
    return fake_redis
