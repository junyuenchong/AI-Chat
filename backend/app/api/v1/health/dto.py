"""Health response DTOs (GET /health has no request body)."""

from pydantic import BaseModel, ConfigDict


class HealthLayersResponse(BaseModel):
    """Human-readable labels for LangChain and RAG layers."""

    model_config = ConfigDict(extra="forbid")

    langchain: str
    rag: str


class HealthResponse(BaseModel):
    """GET /health response — app status and dependency checks."""

    model_config = ConfigDict(extra="forbid")

    status: str
    app: str
    llm: str
    postgres: bool
    redis: bool
    layers: HealthLayersResponse
