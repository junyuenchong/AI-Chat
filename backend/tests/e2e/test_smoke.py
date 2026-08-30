"""End-to-end smoke tests for the main user flows.

In-process by default; set E2E_BASE_URL to run against a live server.
"""

from uuid import uuid4

import pytest
from tests.helpers import auth_headers, chat_complete, chat_stream_events

# ────────────────────────────────────────────────────────────
# test_live_health
# Endpoint: GET /health
# Use: server is up and returns ok or degraded status.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_live_health(live_client):
    response = await live_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}


# ────────────────────────────────────────────────────────────
# test_live_register_chat_flow
# Endpoint: POST /auth/register, POST /chat/complete, GET /conversations
# Use: sign up, send two chat messages, and see the thread in the sidebar list.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_live_register_chat_flow(live_client):
    email = f"e2e-{uuid4().hex}@example.com"
    register = await live_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "E2E User"},
    )
    assert register.status_code == 201
    headers = auth_headers(register.json()["access_token"])

    complete = await chat_complete(live_client, headers, "E2E hello")
    assert complete.status_code == 200
    conversation_id = complete.json()["conversation_id"]

    follow_up = await chat_complete(
        live_client,
        headers,
        "E2E second turn",
        conversation_id=conversation_id,
    )
    assert follow_up.status_code == 200

    conversations = await live_client.get("/api/v1/conversations", headers=headers)
    assert conversations.status_code == 200
    assert len(conversations.json()) >= 1


# ────────────────────────────────────────────────────────────
# test_live_chat_stream_contract
# Endpoint: POST /auth/register, POST /chat/stream
# Use: streaming chat returns meta, token, and done SSE events.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_live_chat_stream_contract(live_client):
    email = f"e2e-sse-{uuid4().hex}@example.com"
    register = await live_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "E2E SSE"},
    )
    assert register.status_code == 201
    headers = auth_headers(register.json()["access_token"])

    response, events = await chat_stream_events(
        live_client,
        headers,
        "E2E stream test",
    )
    assert response.status_code == 200
    names = [e["event"] for e in events]
    assert "meta" in names
    assert "token" in names
    assert "done" in names
