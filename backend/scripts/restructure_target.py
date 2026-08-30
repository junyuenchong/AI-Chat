"""
Restructure app/ to the target clean-architecture layout:

  api/v1/{auth,chat,conversations,documents}/router.py + dto.py
  application/{auth,chat,conversations,documents}/
  domain/{auth,chat,conversations,documents}/
  ai/{chains,prompts,retrieval,tools,providers}/
  infrastructure/{database,vectorstore,redis,external}/
  core/{config,security,exceptions,logging,...}
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
TESTS = ROOT / "tests"

# Longest-prefix-first import rewrites (applied to all .py under backend/)
IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    # schemas → api dto
    ("app.api.v1.auth.dto", "app.api.v1.auth.dto"),
    ("app.api.v1.auth.dto", "app.api.v1.auth.dto"),
    ("app.api.v1.chat.dto", "app.api.v1.chat.dto"),
    ("app.api.v1.chat.dto", "app.api.v1.chat.dto"),
    ("app.api.v1.conversations.dto", "app.api.v1.conversations.dto"),
    ("app.api.v1.documents.dto", "app.api.v1.documents.dto"),
    ("app.api.v1.documents.dto", "app.api.v1.documents.dto"),
    ("app.api.v1.health.dto", "app.api.v1.health.dto"),
    # routers → api
    ("app.api.v1.auth.router", "app.api.v1.auth.router"),
    ("app.api.v1.chat.router", "app.api.v1.chat.router"),
    ("app.api.v1.conversations.router", "app.api.v1.conversations.router"),
    ("app.api.v1.documents.router", "app.api.v1.documents.router"),
    ("app.api.v1.health.router", "app.api.v1.health.router"),
    (
        "from app.api.v1.router import api_router",
        "from app.api.v1.router import api_router",
    ),
    # services → application
    ("app.application.documents", "app.application.documents"),
    ("app.application.auth", "app.application.auth"),
    ("app.application.chat", "app.application.chat"),
    ("app.application.conversations", "app.application.conversations"),
    # prompts / chains
    ("app.ai.prompts.chat", "app.ai.prompts.chat"),
    ("app.ai.prompts.chat", "app.ai.prompts.chat"),
    ("app.ai.chains.chat", "app.ai.chains.chat"),
    ("app.ai.chains.chat", "app.ai.chains.chat"),
    # domain
    ("app.domain", "app.domain"),
    # ai providers / retrieval
    ("app.ai.retrieval.adapter", "app.ai.retrieval.adapter"),
    ("app.ai.providers.langchain", "app.ai.providers.langchain"),
    ("app.ai.providers.demo", "app.ai.providers.demo"),
    ("app.ai.providers.registry", "app.ai.providers.registry"),
    ("app.ai.providers.llm", "app.ai.providers.llm"),
    ("app.ai.providers.errors", "app.ai.providers.errors"),
    ("app.ai.providers", "app.ai.providers"),
    ("app.ai.retrieval.strategies", "app.ai.retrieval.strategies"),
    ("app.ai.retrieval.retriever", "app.ai.retrieval.retriever"),
    ("app.ai.providers.embeddings", "app.ai.providers.embeddings"),
    ("app.ai.retrieval", "app.ai.retrieval"),
    # infrastructure
    (
        "app.infrastructure.database.repositories",
        "app.infrastructure.database.repositories",
    ),
    (
        "app.infrastructure.database.repositories.conversation",
        "app.infrastructure.database.repositories.conversation",
    ),
    (
        "app.infrastructure.database.repositories.document",
        "app.infrastructure.database.repositories.document",
    ),
    (
        "app.infrastructure.database.repositories.user",
        "app.infrastructure.database.repositories.user",
    ),
    (
        "app.infrastructure.database.repositories",
        "app.infrastructure.database.repositories",
    ),
    ("app.infrastructure.database.models", "app.infrastructure.database.models"),
    ("app.infrastructure.database.session", "app.infrastructure.database.session"),
    ("app.infrastructure.redis.session", "app.infrastructure.redis.session"),
    ("app.infrastructure.redis.client", "app.infrastructure.redis.client"),
    ("app.infrastructure.redis", "app.infrastructure.redis"),
    ("app.infrastructure.external.worker", "app.infrastructure.external.worker"),
    ("app.infrastructure.external.queue", "app.infrastructure.external.queue"),
    ("app.infrastructure.external", "app.infrastructure.external"),
    ("app.infrastructure.external.tasks", "app.infrastructure.external.tasks"),
    ("app.infrastructure.external", "app.infrastructure.external"),
    # core
    ("app.core.exceptions", "app.core.exceptions"),
    ("app.core.errors", "app.core.errors"),
    ("app.core.middleware", "app.core.middleware"),
    ("app.core.security", "app.core.security"),
    ("app.core.cookies", "app.core.cookies"),
    ("app.core.logging", "app.core.logging"),
    ("app.infrastructure.database.session", "app.infrastructure.database.session"),
    ("app.core.config", "app.core.config"),
    ("app.core.dependencies", "app.core.dependencies"),
    # knowledge → documents naming
    ("DocumentsService", "DocumentsService"),
    ("DocumentsMapper", "DocumentsMapper"),
    ("get_documents_service", "get_documents_service"),
    ("documents_service", "documents_service"),
]

SYMBOL_REPLACEMENTS: list[tuple[str, str]] = [
    ("DocumentsService", "DocumentsService"),
    ("DocumentsMapper", "DocumentsMapper"),
    ("get_documents_service", "get_documents_service"),
]


def move(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    shutil.move(str(src), str(dst))


def merge_dto(
    feature: str, request: Path | None, response: Path | None, dst: Path
) -> None:
    parts: list[str] = [
        f'"""\n{feature.title()} DTOs.\n\nRequest and response models.\n"""\n'
    ]
    for path in (request, response):
        if path and path.exists():
            text = path.read_text(encoding="utf-8")
            # Drop module docstring
            text = re.sub(r'^"""[\s\S]*?"""\n+', "", text, count=1)
            parts.append(text.strip())
            parts.append("")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def split_prompts(src: Path, chat_dst: Path, summarize_dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    chat_dst.parent.mkdir(parents=True, exist_ok=True)
    summarize_dst.parent.mkdir(parents=True, exist_ok=True)

    chat_parts = [
        '"""Chat prompts — system prompt and RAG context helpers."""\n',
        'SYSTEM_PROMPT = """You are a production AI chat assistant for a FastAPI portfolio stack.',
    ]
    # Re-extract from source for reliability
    if "SYSTEM_PROMPT" in text:
        m = re.search(r'(SYSTEM_PROMPT = """[\s\S]*?""")', text)
        strict = re.search(r"(STRICT_RAG_EMPTY_REPLY = [\s\S]*?\))", text)
        append_fn = re.search(
            r'(def append_rag_context[\s\S]*?return f"\{system_prompt\}\\n\\nRetrieved context:\\n\{rag_context\}")',
            text,
        )
        chat_body = [m.group(1) if m else "", strict.group(1) if strict else "", ""]
        if append_fn:
            chat_body.append(append_fn.group(1))
        chat_dst.write_text(
            '"""Chat prompts — system prompt and RAG context helpers."""\n\n'
            + "\n\n".join(p for p in chat_body if p)
            + "\n",
            encoding="utf-8",
        )

    summarize_body = []
    for name in ("SUMMARIZE_SYSTEM_PROMPT", "SUMMARIZE_USER_PROMPT"):
        m = re.search(rf"({name} = .+)", text)
        if m:
            summarize_body.append(m.group(1))
    summarize_dst.write_text(
        '"""Summarize prompts for conversation summary jobs."""\n\n'
        + "\n\n".join(summarize_body)
        + "\n",
        encoding="utf-8",
    )


def rewrite_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in IMPORT_REPLACEMENTS:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def rewrite_tree(root: Path) -> None:
    if not root.exists():
        return
    for path in root.rglob("*.py"):
        rewrite_file(path)


def remove_empty_dirs(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def main() -> None:
    # --- core ---
    move(APP / "config.py", APP / "core" / "config.py")
    move(APP / "dependencies.py", APP / "core" / "dependencies.py")
    move(APP / "internal" / "security.py", APP / "core" / "security.py")
    move(APP / "internal" / "cookies.py", APP / "core" / "cookies.py")
    move(APP / "internal" / "logging.py", APP / "core" / "logging.py")
    move(APP / "internal" / "middleware.py", APP / "core" / "middleware.py")
    move(APP / "internal" / "errors.py", APP / "core" / "errors.py")
    if (APP / "internal" / "exceptions").exists():
        move(APP / "internal" / "exceptions", APP / "core" / "exceptions")

    # --- infrastructure database ---
    move(APP / "database.py", APP / "infrastructure" / "database" / "session.py")
    if (APP / "models").exists():
        move(APP / "models", APP / "infrastructure" / "database" / "models")
    if (APP / "crud").exists():
        move(APP / "crud", APP / "infrastructure" / "database" / "repositories")

    # --- infrastructure redis ---
    if (APP / "internal" / "cache").exists():
        move(
            APP / "internal" / "cache" / "redis.py",
            APP / "infrastructure" / "redis" / "client.py",
        )
        move(
            APP / "internal" / "cache" / "session.py",
            APP / "infrastructure" / "redis" / "session.py",
        )
        init = APP / "internal" / "cache" / "__init__.py"
        if init.exists():
            init.unlink()

    # --- infrastructure external (queue + jobs) ---
    if (APP / "internal" / "queue").exists():
        move(
            APP / "internal" / "queue" / "queue.py",
            APP / "infrastructure" / "external" / "queue.py",
        )
        move(
            APP / "internal" / "queue" / "worker.py",
            APP / "infrastructure" / "external" / "worker.py",
        )
    if (APP / "internal" / "jobs").exists():
        move(
            APP / "internal" / "jobs" / "tasks.py",
            APP / "infrastructure" / "external" / "tasks.py",
        )

    # --- ai ---
    if (APP / "internal" / "llm").exists():
        move(APP / "internal" / "llm", APP / "ai" / "providers")
    if (APP / "internal" / "vectorstore" / "embeddings.py").exists():
        move(
            APP / "internal" / "vectorstore" / "embeddings.py",
            APP / "ai" / "providers" / "embeddings.py",
        )
    if (APP / "internal" / "vectorstore" / "retriever.py").exists():
        move(
            APP / "internal" / "vectorstore" / "retriever.py",
            APP / "ai" / "retrieval" / "retriever.py",
        )
    if (APP / "internal" / "vectorstore" / "retrieval_strategies.py").exists():
        move(
            APP / "internal" / "vectorstore" / "retrieval_strategies.py",
            APP / "ai" / "retrieval" / "strategies.py",
        )
    if (APP / "internal" / "llm" / "langchain_rag.py").exists():
        pass  # already moved with llm dir — will be at ai/providers/langchain_rag.py
    # langchain_rag after llm move lives in ai/providers/langchain_rag.py → move to adapter
    rag_adapter = APP / "ai" / "providers" / "langchain_rag.py"
    if rag_adapter.exists():
        move(rag_adapter, APP / "ai" / "retrieval" / "adapter.py")

    # pgvector helper — split_text stays in retriever; add thin pgvector module
    pgvector = APP / "infrastructure" / "vectorstore" / "pgvector.py"
    pgvector.parent.mkdir(parents=True, exist_ok=True)
    if not pgvector.exists():
        pgvector.write_text(
            '"""pgvector storage helpers (chunk persistence via SQLAlchemy models)."""\n',
            encoding="utf-8",
        )

    # --- domain ---
    if (APP / "internal" / "domain" / "chat").exists():
        move(APP / "internal" / "domain" / "chat", APP / "domain" / "chat")
    for name in ("auth", "conversations", "documents"):
        d = APP / "domain" / name
        d.mkdir(parents=True, exist_ok=True)
        init = d / "__init__.py"
        if not init.exists():
            init.write_text(f'"""Domain layer — {name}."""\n', encoding="utf-8")

    # --- application ---
    if (APP / "services" / "auth").exists():
        move(APP / "services" / "auth", APP / "application" / "auth")
    if (APP / "services" / "chat").exists():
        move(APP / "services" / "chat", APP / "application" / "chat")
    if (APP / "services" / "conversations").exists():
        move(APP / "services" / "conversations", APP / "application" / "conversations")
    if (APP / "services" / "knowledge").exists():
        move(APP / "services" / "knowledge", APP / "application" / "documents")

    # prompts + chains from application/chat
    prompts_src = APP / "application" / "chat" / "prompts.py"
    if prompts_src.exists():
        split_prompts(
            prompts_src,
            APP / "ai" / "prompts" / "chat.py",
            APP / "ai" / "prompts" / "summarize.py",
        )
        prompts_src.unlink()
    helpers_src = APP / "application" / "chat" / "helpers.py"
    if helpers_src.exists():
        move(helpers_src, APP / "ai" / "chains" / "chat.py")

    # summarize chain stub
    summarize_chain = APP / "ai" / "chains" / "summarize.py"
    if not summarize_chain.exists():
        summarize_chain.parent.mkdir(parents=True, exist_ok=True)
        summarize_chain.write_text(
            '"""Summarize chain — delegates to LLM provider."""\n\n'
            "from app.ai.providers.llm import build_llm_port\n\n\n"
            "async def summarize_transcript(transcript: str) -> str:\n"
            '    """Return a short summary of a conversation transcript."""\n'
            "    return await build_llm_port().summarize(transcript)\n",
            encoding="utf-8",
        )

    # search tool stub (keyword search lives in retriever)
    search_tool = APP / "ai" / "tools" / "search.py"
    if not search_tool.exists():
        search_tool.parent.mkdir(parents=True, exist_ok=True)
        search_tool.write_text(
            '"""Search tools — keyword and vector search via retrieval layer."""\n\n'
            "from app.ai.retrieval.retriever import retrieve_context\n\n"
            '__all__ = ["retrieve_context"]\n',
            encoding="utf-8",
        )

    # rename factory.py → llm.py in providers (keep build_llm_port)
    factory = APP / "ai" / "providers" / "factory.py"
    llm_mod = APP / "ai" / "providers" / "llm.py"
    if factory.exists() and not llm_mod.exists():
        move(factory, llm_mod)
    registry = APP / "ai" / "providers" / "provider_registry.py"
    if registry.exists():
        move(registry, APP / "ai" / "providers" / "registry.py")

    # --- api v1 routers ---
    router_map = {
        "auth": APP / "routers" / "auth.py",
        "chat": APP / "routers" / "chat.py",
        "conversations": APP / "routers" / "conversations.py",
        "documents": APP / "routers" / "knowledge.py",
        "health": APP / "routers" / "health.py",
    }
    for name, src in router_map.items():
        if src.exists():
            move(src, APP / "api" / "v1" / name / "router.py")

    # merge dto
    merge_dto(
        "auth",
        APP / "schemas" / "auth" / "request.py",
        APP / "schemas" / "auth" / "response.py",
        APP / "api" / "v1" / "auth" / "dto.py",
    )
    merge_dto(
        "chat",
        APP / "schemas" / "chat" / "request.py",
        APP / "schemas" / "chat" / "response.py",
        APP / "api" / "v1" / "chat" / "dto.py",
    )
    merge_dto(
        "conversations",
        None,
        APP / "schemas" / "conversations" / "response.py",
        APP / "api" / "v1" / "conversations" / "dto.py",
    )
    merge_dto(
        "documents",
        APP / "schemas" / "knowledge" / "request.py",
        APP / "schemas" / "knowledge" / "response.py",
        APP / "api" / "v1" / "documents" / "dto.py",
    )
    merge_dto(
        "health",
        None,
        APP / "schemas" / "health" / "response.py",
        APP / "api" / "v1" / "health" / "dto.py",
    )

    # api v1 router
    old_router_init = APP / "routers" / "__init__.py"
    if old_router_init.exists():
        text = old_router_init.read_text(encoding="utf-8")
        text = text.replace(
            "app.api.v1.documents.router", "app.api.v1.documents.router"
        )
        text = text.replace("app.routers.", "app.api.v1.")
        text = text.replace("knowledge_router", "documents_router")
        text = text.replace(
            "from app.api.v1.documents import router as documents_router",
            "from app.api.v1.documents.router import router as documents_router",
        )
        for feat in ("auth", "chat", "conversations", "health"):
            text = text.replace(
                f"from app.api.v1.{feat} import router as {feat}_router",
                f"from app.api.v1.{feat}.router import router as {feat}_router",
            )
        (APP / "api" / "v1" / "router.py").parent.mkdir(parents=True, exist_ok=True)
        (APP / "api" / "v1" / "router.py").write_text(text, encoding="utf-8")

    # package __init__ files
    for pkg in [
        APP / "core",
        APP / "api" / "v1",
        APP / "application",
        APP / "domain",
        APP / "ai",
        APP / "ai" / "chains",
        APP / "ai" / "prompts",
        APP / "ai" / "retrieval",
        APP / "ai" / "tools",
        APP / "ai" / "providers",
        APP / "infrastructure",
        APP / "infrastructure" / "database",
        APP / "infrastructure" / "vectorstore",
        APP / "infrastructure" / "redis",
        APP / "infrastructure" / "external",
    ]:
        pkg.mkdir(parents=True, exist_ok=True)
        init = pkg / "__init__.py"
        if not init.exists():
            init.write_text(f'"""{pkg.name} package."""\n', encoding="utf-8")

    # update app/__init__.py
    app_init = APP / "__init__.py"
    app_init.write_text(
        '"""Application package root."""\n\n'
        "from app.core.config import get_settings\n\n"
        '__all__ = ["get_settings"]\n',
        encoding="utf-8",
    )

    # rewrite imports everywhere
    rewrite_tree(APP)
    rewrite_tree(TESTS)
    rewrite_tree(ROOT / "alembic")
    rewrite_tree(ROOT / "scripts")

    # fix main.py imports explicitly
    main = APP / "main.py"
    if main.exists():
        text = main.read_text(encoding="utf-8")
        text = text.replace(
            "from app.api.v1.router import api_router",
            "from app.api.v1.router import api_router",
        )
        text = text.replace(
            "from app.infrastructure.redis.client",
            "from app.infrastructure.redis.client",
        )
        text = text.replace(
            "from app.infrastructure.external.queue",
            "from app.infrastructure.external.queue",
        )
        main.write_text(text, encoding="utf-8")
        rewrite_file(main)

    # fix external tasks imports for summarize chain
    tasks = APP / "infrastructure" / "external" / "tasks.py"
    if tasks.exists():
        text = tasks.read_text(encoding="utf-8")
        text = text.replace(
            "from app.ai.retrieval.retriever import split_text",
            "from app.ai.retrieval.retriever import split_text",
        )
        text = text.replace(
            "summary = await build_llm_port().summarize(transcript)",
            "from app.ai.chains.summarize import summarize_transcript\n"
            "            summary = await summarize_transcript(transcript)",
        )
        tasks.write_text(text, encoding="utf-8")

    # documents router tag
    doc_router = APP / "api" / "v1" / "documents" / "router.py"
    if doc_router.exists():
        text = doc_router.read_text(encoding="utf-8")
        text = text.replace('tags=["knowledge"]', 'tags=["documents"]')
        doc_router.write_text(text, encoding="utf-8")

    # cleanup legacy dirs
    for legacy in (
        "routers",
        "schemas",
        "services",
        "models",
        "crud",
        "internal",
    ):
        legacy_path = APP / legacy
        if legacy_path.exists():
            shutil.rmtree(legacy_path)

    # reorganize tests
    unit = TESTS / "unit"
    unit.mkdir(exist_ok=True)
    for sub in ("api", "ai", "services"):
        src = TESTS / sub
        if src.exists():
            dst = unit / sub
            if dst.exists():
                shutil.rmtree(dst)
            move(src, dst)

    remove_empty_dirs(APP)
    print("Restructure complete.")


if __name__ == "__main__":
    main()
