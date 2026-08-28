"""Build the active LLMPort implementation from settings."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.domain.chat.ports import LLMPort
from app.infrastructure.llm.demo.provider import DemoProvider
from app.infrastructure.llm.langchain.provider import LangChainProvider
from app.infrastructure.llm.provider_registry import build_chat_model_chain


def build_llm_port(settings: Settings | None = None) -> LLMPort:
    """Return DemoProvider when no keys are set; otherwise LangChain with fallbacks."""
    cfg = settings or get_settings()
    if not cfg.llm_enabled:
        return DemoProvider()
    chain = build_chat_model_chain(cfg)
    if not chain:
        return DemoProvider()
    return LangChainProvider(chain)
