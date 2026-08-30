"""Unit tests for API route registration.

No database — confirms all v1 endpoints are mounted on the app.
"""

from app.api.v1.router import api_router
from app.main import create_app

# ────────────────────────────────────────────────────────────
# test_v1_routes_are_mounted
# Endpoint: GET /health, POST /auth/login, POST /chat/stream, GET /conversations
# Use: confirm core feature routes exist in the OpenAPI schema after app startup.
# ────────────────────────────────────────────────────────────


def test_v1_routes_are_mounted():
    paths = set(create_app().openapi()["paths"])
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/chat/stream" in paths
    assert "/api/v1/conversations" in paths
    assert "/api/v1/health" in paths
    assert api_router.routes


# ────────────────────────────────────────────────────────────
# test_app_uses_v1_prefix
# Endpoint: all /api/v1/* routes
# Use: every documented API path stays under the /api/v1 version prefix.
# ────────────────────────────────────────────────────────────


def test_app_uses_v1_prefix():
    paths = set(create_app().openapi()["paths"])
    assert all(path.startswith("/api/v1/") for path in paths)
