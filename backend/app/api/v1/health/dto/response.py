"""
Health response DTOs.

Pydantic models for GET /health.
"""

from pydantic import BaseModel, ConfigDict


# ────────────────────────────────────────────────────────
# HealthLayersResponse
# Internal — nested layer labels inside GET /health response.
# Provides human-readable names for the LangChain and RAG layers.
# ────────────────────────────────────────────────────────
class HealthLayersResponse(BaseModel):
    """Human-readable labels for LangChain and RAG layers."""

    model_config = ConfigDict(extra="forbid")

    langchain: str
    rag: str


# ────────────────────────────────────────────────────────
# HealthResponse
# Internal — GET /health response body.
# Reports app status and results of dependency health checks.
# ────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """GET /health response — app status and dependency checks."""

    model_config = ConfigDict(extra="forbid")

    status: str
    app: str
    llm: str
    postgres: bool
    redis: bool
    layers: HealthLayersResponse
