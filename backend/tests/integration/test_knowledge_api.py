"""Integration tests for knowledge document endpoints.

Requires Postgres — upload, list, and RAG chat with uploaded content.
"""

from uuid import uuid4

import pytest
from tests.helpers import auth_headers, register_user

# ────────────────────────────────────────────────────────────
# test_create_and_list_document
# Endpoint: POST /documents, GET /documents
# Use: upload a document and see it in the knowledge page list.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_list_document(api_client):
    registered = await register_user(api_client, email=f"doc-{uuid4().hex}@example.com")
    headers = auth_headers(registered["access_token"])

    created = await api_client.post(
        "/api/v1/documents",
        headers=headers,
        json={
            "filename": "policy.md",
            "content": "Annual leave policy: employees receive 14 days per year.",
        },
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]

    listed = await api_client.get("/api/v1/documents", headers=headers)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()}
    assert doc_id in ids
    assert "content" not in listed.json()[0]  # List response shows metadata only.


# ────────────────────────────────────────────────────────────
# test_chat_with_rag_uses_knowledge
# Endpoint: POST /documents, POST /chat/complete
# Use: chat with use_rag=true returns a reply after a document is uploaded.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_with_rag_uses_knowledge(api_client):
    registered = await register_user(api_client, email=f"rag-{uuid4().hex}@example.com")
    headers = auth_headers(registered["access_token"])

    await api_client.post(
        "/api/v1/documents",
        headers=headers,
        json={
            "filename": "handbook.md",
            "content": "UniqueKeywordXYZ annual leave is exactly 21 days for all staff.",
        },
    )

    complete = await api_client.post(
        "/api/v1/chat/complete",
        headers=headers,
        json={"message": "What is UniqueKeywordXYZ annual leave?", "use_rag": True},
    )
    assert complete.status_code == 200
    assert complete.json()["content"]
