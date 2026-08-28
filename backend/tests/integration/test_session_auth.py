"""Integration tests for session cookie authentication.

Requires Postgres and Redis — register, cookie session, and logout flow.
"""

from uuid import uuid4

import pytest
from app.core.config import get_settings

# ────────────────────────────────────────────────────────────
# test_login_sets_session_cookie_and_me_works
# Endpoint: POST /auth/register, GET /auth/me
# Use: sign-up sets an HttpOnly session cookie so GET /auth/me works without Bearer token.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_sets_session_cookie_and_me_works(api_client):
    email = f"cookie-{uuid4().hex}@example.com"
    login = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Cookie User"},
    )
    assert login.status_code == 201
    cookie_name = get_settings().session_cookie_name
    assert cookie_name in login.cookies

    me = await api_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == email


# ────────────────────────────────────────────────────────────
# test_logout_clears_session
# Endpoint: POST /auth/register, POST /auth/logout, GET /auth/me
# Use: logout clears the session cookie and blocks access to GET /auth/me.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_logout_clears_session(api_client):
    email = f"logout-{uuid4().hex}@example.com"
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Logout User"},
    )
    logout = await api_client.post("/api/v1/auth/logout")
    assert logout.status_code == 204

    me = await api_client.get("/api/v1/auth/me")
    assert me.status_code == 401
