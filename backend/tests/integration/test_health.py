"""Integration tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_returns_dependency_flags(api_client):
    response = await api_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "llm" in body
    assert "postgres" in body
