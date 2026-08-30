"""Integration tests for chat endpoints.

Requires Postgres — auth, validation, persistence, SSE stream, and rate limits.
"""

from uuid import uuid4

import pytest
from tests.helpers import auth_headers, chat_complete, chat_stream_events, register_user

# ────────────────────────────────────────────────────────────
# test_chat_complete_without_token_returns_401
# Endpoint: POST /chat/complete
# Use: chat requires login — unauthenticated request returns 401.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_complete_without_token_returns_401(api_client):
    response = await api_client.post(
        "/api/v1/chat/complete",
        json={"message": "hello"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


# ────────────────────────────────────────────────────────────
# test_chat_stream_without_token_returns_401
# Endpoint: POST /chat/stream
# Use: streaming chat requires login — unauthenticated request returns 401.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_stream_without_token_returns_401(api_client):
    response = await api_client.post(
        "/api/v1/chat/stream",
        json={"message": "hello"},
    )
    assert response.status_code == 401


# ────────────────────────────────────────────────────────────
# test_chat_complete_blank_message_returns_422
# Endpoint: POST /chat/complete
# Use: empty message is rejected with a field error before AI runs.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_complete_blank_message_returns_422(api_client, auth_user):
    response = await chat_complete(api_client, auth_user["headers"], "   ")
    assert response.status_code == 422
    fields = {f["field"] for f in response.json()["error"]["fields"]}
    assert "message" in fields


# ────────────────────────────────────────────────────────────
# test_chat_complete_persists_conversation
# Endpoint: POST /chat/complete, GET /conversations/{id}
# Use: one chat turn saves user and assistant messages to the thread.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_complete_persists_conversation(api_client, auth_user):
    response = await chat_complete(
        api_client,
        auth_user["headers"],
        "Hello from integration test",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"]
    assert body["llm"] in {"demo", "gemini", "openai"}

    detail = await api_client.get(
        f"/api/v1/conversations/{body['conversation_id']}",
        headers=auth_user["headers"],
    )
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello from integration test"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"]


# ────────────────────────────────────────────────────────────
# test_chat_multi_turn_same_conversation_id
# Endpoint: POST /chat/complete, GET /conversations/{id}
# Use: follow-up messages append to the same thread when conversation_id is sent.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_multi_turn_same_conversation_id(api_client, auth_user):
    first = await chat_complete(
        api_client, auth_user["headers"], "First turn question"
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    second = await chat_complete(
        api_client,
        auth_user["headers"],
        "Second turn follow-up",
        conversation_id=conversation_id,
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id

    detail = await api_client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_user["headers"],
    )
    messages = detail.json()["messages"]
    assert len(messages) == 4
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Second turn follow-up"
    assert messages[3]["role"] == "assistant"


# ────────────────────────────────────────────────────────────
# test_chat_unknown_conversation_id_returns_404
# Endpoint: POST /chat/complete
# Use: chatting in a non-existent thread returns 404 CONVERSATION_NOT_FOUND.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_unknown_conversation_id_returns_404(api_client, auth_user):
    response = await chat_complete(
        api_client,
        auth_user["headers"],
        "hello",
        conversation_id=str(uuid4()),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


# ────────────────────────────────────────────────────────────
# test_chat_other_users_conversation_returns_404
# Endpoint: POST /chat/complete
# Use: users cannot send messages into another user's conversation.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_other_users_conversation_returns_404(api_client, auth_user):
    other = await register_user(api_client, email=f"other-{uuid4().hex}@example.com")
    owned = await chat_complete(
        api_client,
        auth_headers(other["access_token"]),
        "private thread",
    )
    conversation_id = owned.json()["conversation_id"]

    response = await chat_complete(
        api_client,
        auth_user["headers"],
        "try to hijack",
        conversation_id=conversation_id,
    )
    assert response.status_code == 404


# ────────────────────────────────────────────────────────────
# test_chat_complete_returns_reply
# Endpoint: POST /chat/complete
# Use: chat returns a reply for a normal question.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_complete_returns_reply(api_client, auth_user):
    response = await chat_complete(
        api_client,
        auth_user["headers"],
        "Hello from integration test",
    )
    assert response.status_code == 200
    assert response.json()["content"]


# ────────────────────────────────────────────────────────────
# test_chat_stream_emits_meta_token_done
# Endpoint: POST /chat/stream, GET /conversations/{id}
# Use: SSE stream sends meta, tokens, and done events; messages are saved.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_stream_emits_meta_token_done(api_client, auth_user):
    response, events = await chat_stream_events(
        api_client,
        auth_user["headers"],
        "Stream hello",
    )
    assert response.status_code == 200
    names = [e["event"] for e in events]
    assert names[0] == "meta"
    assert "token" in names
    assert names[-1] == "done"

    meta = events[0]["data"]
    assert meta["conversation_id"]
    assert meta["llm"] in {"demo", "gemini", "openai"}
    assert meta["route"] == "chat"
    assert meta["components"] == "langchain"

    done = events[-1]["data"]
    assert done["content"]
    assert done["conversation_id"] == meta["conversation_id"]

    detail = await api_client.get(
        f"/api/v1/conversations/{meta['conversation_id']}",
        headers=auth_user["headers"],
    )
    assert len(detail.json()["messages"]) == 2


# ────────────────────────────────────────────────────────────
# test_chat_stream_unknown_conversation_emits_error_event
# Endpoint: POST /chat/stream
# Use: streaming into a missing thread sends an SSE error event, not HTTP 404.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_stream_unknown_conversation_emits_error_event(
    api_client, auth_user
):
    response, events = await chat_stream_events(
        api_client,
        auth_user["headers"],
        "hello",
        conversation_id=str(uuid4()),
    )
    assert response.status_code == 200
    assert any(e["event"] == "error" for e in events)
    error = next(e for e in events if e["event"] == "error")
    assert error["data"]["code"] == "CONVERSATION_NOT_FOUND"


