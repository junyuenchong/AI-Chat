"""Shared helpers for integration and end-to-end API tests."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from httpx import AsyncClient, Response

# ────────────────────────────────────────────────────────────
# register_user
# Endpoint: POST /auth/register
# Use: create a test user and return the token response body.
# ────────────────────────────────────────────────────────────


async def register_user(
    client: AsyncClient,
    *,
    email: str | None = None,
    password: str = "testpass123",
    name: str = "Test User",
) -> dict[str, Any]:
    payload = {
        "email": email or f"user-{uuid4().hex}@example.com",
        "password": password,
        "name": name,
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ────────────────────────────────────────────────────────────
# auth_headers
# Endpoint: all protected routes
# Use: build Authorization Bearer header from a JWT access token.
# ────────────────────────────────────────────────────────────


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ────────────────────────────────────────────────────────────
# patch_get_redis
# Internal — test setup
# Use: replace Redis with FakeRedis in every module that imports get_redis.
# ────────────────────────────────────────────────────────────


def patch_get_redis(monkeypatch, fake: FakeRedis) -> None:
    targets = (
        "app.infrastructure.cache.redis.get_redis",
        "app.core.middleware.get_redis",
        "app.application.chat.service.get_redis",
        "app.infrastructure.cache.session.get_redis",
        "app.api.v1.health.router.get_redis",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _fake=fake: _fake)


# ────────────────────────────────────────────────────────────
# _use_bearer_only
# Internal — test helper
# Use: clear session cookies so Bearer token auth is tested in isolation.
# ────────────────────────────────────────────────────────────


def _use_bearer_only(client: AsyncClient, headers: dict[str, str]) -> None:
    if "Authorization" in headers:
        client.cookies.clear()


# ────────────────────────────────────────────────────────────
# chat_complete
# Endpoint: POST /chat/complete
# Use: send one non-streaming chat message and return the HTTP response.
# ────────────────────────────────────────────────────────────


async def chat_complete(
    client: AsyncClient,
    headers: dict[str, str],
    message: str,
    *,
    conversation_id: str | None = None,
    use_rag: bool = False,
) -> Response:
    body: dict[str, Any] = {"message": message, "use_rag": use_rag}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    _use_bearer_only(client, headers)
    return await client.post("/api/v1/chat/complete", headers=headers, json=body)


# ────────────────────────────────────────────────────────────
# chat_stream_events
# Endpoint: POST /chat/stream
# Use: open an SSE stream, collect all events, and return them with the response.
# ────────────────────────────────────────────────────────────


async def chat_stream_events(
    client: AsyncClient,
    headers: dict[str, str],
    message: str,
    *,
    conversation_id: str | None = None,
    use_rag: bool = False,
) -> tuple[Response, list[dict]]:
    body: dict[str, Any] = {"message": message, "use_rag": use_rag}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    _use_bearer_only(client, headers)
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        headers=headers,
        json=body,
    ) as response:
        events = await collect_sse_events(response)
        return response, events


# ────────────────────────────────────────────────────────────
# collect_sse_events
# Endpoint: POST /chat/stream (internal)
# Use: parse raw SSE lines into a list of {event, data} dicts.
# ────────────────────────────────────────────────────────────


async def collect_sse_events(response) -> list[dict]:
    events: list[dict] = []
    current: dict = {}
    async for line in response.aiter_lines():
        if line.startswith("event:"):
            current["event"] = line[6:].strip()
        elif line.startswith("data:"):
            raw = line[5:].strip()
            try:
                current["data"] = json.loads(raw)
            except json.JSONDecodeError:
                current["data"] = raw
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


class FakeRedis:
    """In-memory Redis stand-in for rate-limit and session tests."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._store: dict[str, str] = {}

    async def ping(self) -> bool:
        return True

    async def incr(self, key: str) -> int:
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        return True

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        self._store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0
