"""Shared helpers for integration and end-to-end API tests."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from httpx import AsyncClient, Response


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


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def chat_complete(
    client: AsyncClient,
    headers: dict[str, str],
    message: str,
    *,
    conversation_id: str | None = None,
) -> Response:
    body: dict[str, Any] = {"message": message}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    return await client.post("/api/v1/chat/complete", headers=headers, json=body)


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


async def chat_stream_events(
    client: AsyncClient,
    headers: dict[str, str],
    message: str,
    *,
    conversation_id: str | None = None,
) -> tuple[Response, list[dict]]:
    body: dict[str, Any] = {"message": message}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        headers=headers,
        json=body,
    ) as response:
        events = await collect_sse_events(response)
        return response, events
