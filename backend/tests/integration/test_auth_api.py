"""Integration tests for auth endpoints.

Requires Postgres — register, login, profile, and protected route access.
"""

from uuid import uuid4

import pytest
from tests.helpers import auth_headers, register_user

# ────────────────────────────────────────────────────────────
# test_register_login_and_me
# Endpoint: POST /auth/register, POST /auth/login, GET /auth/me
# Use: full auth flow — sign up, log in, and load profile with the token.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_login_and_me(api_client):
    registered = await register_user(
        api_client, email=f"auth-{uuid4().hex}@example.com"
    )
    token = registered["access_token"]

    me = await api_client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["email"] == registered["email"]

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": registered["email"], "password": "testpass123"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


# ────────────────────────────────────────────────────────────
# test_duplicate_register_returns_conflict
# Endpoint: POST /auth/register
# Use: signing up with an existing email returns 409 CONFLICT.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicate_register_returns_conflict(api_client):
    email = f"dup-{uuid4().hex}@example.com"
    await register_user(api_client, email=email)
    again = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Dup"},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "CONFLICT"


# ────────────────────────────────────────────────────────────
# test_protected_route_without_token_returns_401
# Endpoint: GET /conversations
# Use: unauthenticated requests to protected routes return 401 UNAUTHORIZED.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401(api_client):
    response = await api_client.get("/api/v1/conversations")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
