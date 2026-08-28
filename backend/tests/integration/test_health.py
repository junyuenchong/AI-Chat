"""Integration tests for the health check endpoint.

Requires Postgres — verifies dependency status flags in the response.
"""

import pytest

# ────────────────────────────────────────────────────────────
# test_health_returns_dependency_flags
# Endpoint: GET /health
# Use: status page shows ok/degraded and reports llm, postgres, redis, layers.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_returns_dependency_flags(api_client):
    response = await api_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "llm" in body
    assert "postgres" in body
    assert "redis" in body
    assert "layers" in body
    assert "langchain" in body["layers"]
    assert "rag" in body["layers"]
