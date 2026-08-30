"""Integration tests for JWT authentication."""

from uuid import uuid4

import pytest
from tests.helpers import auth_headers, register_user


@pytest.mark.asyncio
async def test_register_returns_bearer_token(api_client):
    email = f"jwt-{uuid4().hex}@example.com"
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "JWT User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["email"] == email


@pytest.mark.asyncio
async def test_me_requires_bearer_token(api_client):
    email = f"me-{uuid4().hex}@example.com"
    registered = await register_user(api_client, email=email)
    headers = auth_headers(registered["access_token"])

    me = await api_client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email

    unauthorized = await api_client.get("/api/v1/auth/me")
    assert unauthorized.status_code == 401
