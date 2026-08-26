"""Route map smoke tests (no database).

Confirms /api/v1 feature routes are registered after the app restructure.
"""

from app.api.v1.router import api_router
from app.main import create_app


# ---------------------------------------------------------------------------
# OpenAPI paths — nested include_router does not flatten route.path; use schema.
# ---------------------------------------------------------------------------

def test_v1_routes_are_mounted():
    paths = set(create_app().openapi()["paths"])
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/chat/stream" in paths
    assert "/api/v1/conversations" in paths
    assert "/api/v1/documents" in paths
    assert "/api/v1/health" in paths
    assert api_router.routes  # wiring list is non-empty


# ---------------------------------------------------------------------------
# Versioning — every documented API path stays under /api/v1/.
# ---------------------------------------------------------------------------

def test_app_uses_v1_prefix():
    paths = set(create_app().openapi()["paths"])
    assert all(path.startswith("/api/v1/") for path in paths)
