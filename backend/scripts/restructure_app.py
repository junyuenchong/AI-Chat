"""One-shot migration: legacy layout → modules + infrastructure."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

IMPORT_REPLACEMENTS = [
    (r"\bapp\.models\b", "app.infrastructure.database.models"),
    (r"\bapp\.db\.session\b", "app.infrastructure.database.session"),
    (r"\bapp\.db\.conversation\b", "app.modules.conversations.repository"),
    (r"\bapp\.db\.message\b", "app.modules.conversations.repository"),
    (r"\bapp\.db\.document\b", "app.modules.knowledge.repository"),
    (r"\bapp\.db\.user\b", "app.modules.auth.repository"),
    (r"\bapp\.services\.chat\b", "app.modules.chat.service"),
    (r"\bapp\.services\.conversation\b", "app.modules.conversations.service"),
    (r"\bapp\.services\.knowledge\b", "app.modules.knowledge.service"),
    (r"\bapp\.services\.auth\b", "app.modules.auth.service"),
    (r"\bapp\.clients\.redis\b", "app.infrastructure.cache.redis"),
    (r"\bapp\.clients\.session\b", "app.infrastructure.cache.session"),
    (r"\bapp\.clients\.queue\b", "app.infrastructure.queue.queue"),
    (r"\bapp\.jobs\.tasks\b", "app.infrastructure.jobs.tasks"),
    (r"\bapp\.jobs\.worker\b", "app.infrastructure.queue.worker"),
    (r"\bapp\.ai\.llm\.factory\b", "app.infrastructure.ai.llm"),
    (r"\bapp\.ai\.llm\.providers\b", "app.modules.chat.providers"),
    (r"\bapp\.ai\.prompts\.chat\b", "app.modules.chat.prompts"),
    (r"\bapp\.ai\.prompts\.rag\b", "app.modules.chat.prompts"),
    (r"\bapp\.ai\.rag\.embeddings\b", "app.modules.knowledge.embeddings"),
    (r"\bapp\.ai\.rag\.retrieve\b", "app.modules.knowledge.retriever"),
    (r"\bapp\.ai\.rag\.pgvector\b", "app.modules.knowledge.retriever"),
    (r"\bapp\.ai\.rag\.service\b", "app.modules.knowledge.retriever"),
    (r"\bapp\.ai\.chat\b", "app.modules.chat.service"),
    (r"\bapp\.api\.v1\.(\w+)\.dto\b", r"app.api.v1.\1.schemas"),
]

DTO_TO_SCHEMAS = [
    "auth",
    "chat",
    "conversations",
    "health",
    "knowledge",
]


def apply_imports(content: str) -> str:
    for pattern, repl in IMPORT_REPLACEMENTS:
        content = re.sub(pattern, repl, content)
    return content


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(apply_imports(content), encoding="utf-8")


def copy_transform(src: Path, dst: Path) -> None:
    write(dst, src.read_text(encoding="utf-8"))


def merge_prompts() -> str:
    chat = (APP / "ai/prompts/chat.py").read_text(encoding="utf-8")
    rag = (APP / "ai/prompts/rag.py").read_text(encoding="utf-8")
    # Drop module docstring from rag, keep constants.
    rag_body = "\n".join(
        line
        for line in rag.splitlines()
        if not line.startswith('"""') and line != '"""'
    ).strip()
    return chat.rstrip() + "\n\n\n" + rag_body + "\n"


def merge_repository_conversations() -> str:
    conv = (APP / "db/conversation.py").read_text(encoding="utf-8")
    msg = (APP / "db/message.py").read_text(encoding="utf-8")
    msg = msg.replace('"""Message queries for chat history and persistence."""\n\n', "")
    msg = msg.replace("from app.models.message import Message\n\n", "")
    return (
        '"""Conversation and message persistence."""\n\n'
        + conv.split("\n", 1)[1]
        + "\n\n"
        + msg
    )


def merge_chat_service() -> str:
    svc = (APP / "services/chat.py").read_text(encoding="utf-8")
    ai = (APP / "ai/chat.py").read_text(encoding="utf-8")
    ai = ai.replace(
        '"""Chat AI flow: optional RAG retrieve, then LLM stream or complete."""\n\n',
        "",
    )
    ai = ai.replace(
        "from app.ai.llm.providers import complete_reply, stream_reply\n"
        "from app.ai.rag.retrieve import retrieve_context\n\n",
        "from app.modules.chat.providers import complete_reply, stream_reply\n"
        "from app.modules.knowledge.retriever import retrieve_context\n\n",
    )
    ai = ai.replace(
        "from app.api.v1.chat.dto import",
        "from app.api.v1.chat.schemas import",
    )
    ai = ai.replace(
        "from app.modules.chat.service import run_chat, stream_chat\n",
        "",
    )
    svc = svc.replace(
        "from app.modules.chat.service import run_chat, stream_chat\n",
        "",
    )
    svc = svc.replace(
        "from app.api.v1.chat.dto import",
        "from app.api.v1.chat.schemas import",
    )
    return svc.rstrip() + "\n\n\n" + ai


def merge_retriever() -> str:
    retrieve = (APP / "ai/rag/retrieve.py").read_text(encoding="utf-8")
    pgvector = (APP / "ai/rag/pgvector.py").read_text(encoding="utf-8")
    chunker = (APP / "ai/rag/service.py").read_text(encoding="utf-8")
    pgvector = pgvector.replace(
        '"""pgvector similarity search over document_chunks."""\n\n', ""
    )
    pgvector = pgvector.replace(
        "from app.models.document import Document, DocumentChunk\n\n",
        "",
    )
    chunker = chunker.replace(
        '"""Split document text into overlapping chunks for ingest and embedding."""\n\n\n',
        "",
    )
    return (
        retrieve.replace(
            "from app.ai.rag.embeddings import get_embeddings\n"
            "from app.ai.rag.pgvector import search_similar_chunks\n",
            "from app.modules.knowledge.embeddings import get_embeddings\n",
        )
        + "\n\n"
        + pgvector
        + "\n\n"
        + chunker
    )


def merge_langchain() -> str:
    providers = (APP / "ai/llm/providers.py").read_text(encoding="utf-8")
    start = providers.index("def build_lc_messages")
    end = providers.index("def demo_reply")
    block = providers[start:end]
    return (
        '"""LangChain message builders shared by chat providers and jobs."""\n\n'
        "from __future__ import annotations\n\n"
        "from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage\n\n"
        "from app.modules.chat.prompts import SYSTEM_PROMPT, with_rag_context\n\n\n"
        + block
        + "\n\n"
        + providers[
            providers.index("def _chunk_text") : providers.index("def demo_reply")
        ].replace("def _chunk_text", "def chunk_text")
        + "\n"
    )


def merge_providers() -> str:
    providers = (APP / "ai/llm/providers.py").read_text(encoding="utf-8")
    providers = providers.replace(
        "from app.ai.llm.factory import get_chat_model\n"
        "from app.ai.prompts.chat import SYSTEM_PROMPT, with_rag_context\n"
        "from app.ai.prompts.rag import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT\n\n\n"
        "def build_lc_messages(\n"
        "    history: list[tuple[str, str]],\n"
        "    user_message: str,\n"
        "    rag_context: str | None = None,\n"
        ") -> list[BaseMessage]:\n"
        '    """Build LangChain messages: system (+ RAG) + recent history + user turn."""\n'
        "    messages: list[BaseMessage] = [SystemMessage(content=with_rag_context(SYSTEM_PROMPT, rag_context))]\n"
        "    # Keep a short window so prompts stay within model context limits.\n"
        "    for role, content in history[-12:]:\n"
        '        if role == "user":\n'
        "            messages.append(HumanMessage(content=content))\n"
        '        elif role == "assistant":\n'
        "            messages.append(AIMessage(content=content))\n"
        "    messages.append(HumanMessage(content=user_message))\n"
        "    return messages\n\n\n"
        "def _chunk_text(content: object) -> str:\n"
        "    if isinstance(content, str):\n"
        "        return content\n"
        "    if isinstance(content, list):\n"
        "        parts: list[str] = []\n"
        "        for part in content:\n"
        "            if isinstance(part, str):\n"
        "                parts.append(part)\n"
        '            elif isinstance(part, dict) and part.get("type") == "text":\n'
        '                parts.append(str(part.get("text", "")))\n'
        '        return "".join(parts)\n'
        '    return ""\n\n\n',
        "from app.infrastructure.ai.langchain import build_lc_messages, chunk_text\n"
        "from app.infrastructure.ai.llm import get_chat_model\n"
        "from app.modules.chat.prompts import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT\n\n\n",
    )
    providers = providers.replace(
        "_chunk_text(chunk.content)", "chunk_text(chunk.content)"
    )
    return providers


def main() -> None:
    # --- infrastructure/database/models ---
    for name in ("base", "user", "conversation", "message", "document"):
        copy_transform(
            APP / f"models/{name}.py", APP / f"infrastructure/database/models/{name}.py"
        )

    models_init = '''"""ORM models — call load_models() before create_all."""

from app.infrastructure.database.models.base import Base


def load_models() -> None:
    from app.infrastructure.database.models import (  # noqa: F401
        conversation,
        document,
        message,
        user,
    )


__all__ = ["Base", "load_models"]
'''
    write(APP / "infrastructure/database/models/__init__.py", models_init)
    copy_transform(APP / "db/session.py", APP / "infrastructure/database/session.py")

    # --- infrastructure/ai ---
    copy_transform(APP / "ai/llm/factory.py", APP / "infrastructure/ai/llm.py")
    write(APP / "infrastructure/ai/langchain.py", merge_langchain())
    write(APP / "infrastructure/ai/__init__.py", '"""Shared AI infrastructure."""\n')

    # --- infrastructure/cache & queue ---
    copy_transform(APP / "clients/redis.py", APP / "infrastructure/cache/redis.py")
    copy_transform(APP / "clients/session.py", APP / "infrastructure/cache/session.py")
    copy_transform(APP / "clients/queue.py", APP / "infrastructure/queue/queue.py")
    copy_transform(APP / "jobs/worker.py", APP / "infrastructure/queue/worker.py")

    # --- infrastructure/jobs ---
    copy_transform(APP / "jobs/tasks.py", APP / "infrastructure/jobs/tasks.py")

    # --- modules ---
    copy_transform(APP / "services/auth.py", APP / "modules/auth/service.py")
    copy_transform(APP / "db/user.py", APP / "modules/auth/repository.py")
    write(APP / "modules/chat/prompts.py", merge_prompts())
    write(APP / "modules/chat/providers.py", merge_providers())
    write(APP / "modules/chat/service.py", merge_chat_service())
    copy_transform(
        APP / "services/conversation.py", APP / "modules/conversations/service.py"
    )
    write(APP / "modules/conversations/repository.py", merge_repository_conversations())
    copy_transform(APP / "services/knowledge.py", APP / "modules/knowledge/service.py")
    copy_transform(APP / "db/document.py", APP / "modules/knowledge/repository.py")
    copy_transform(
        APP / "ai/rag/embeddings.py", APP / "modules/knowledge/embeddings.py"
    )
    write(APP / "modules/knowledge/retriever.py", merge_retriever())

    # --- API schemas rename ---
    for feature in DTO_TO_SCHEMAS:
        dto = APP / f"api/v1/{feature}/dto.py"
        if dto.exists():
            copy_transform(dto, APP / f"api/v1/{feature}/schemas.py")

    # --- Update remaining app files in place ---
    for path in list(APP.rglob("*.py")):
        rel = path.relative_to(APP)
        if rel.parts[0] in {"ai", "db", "models", "services", "clients", "jobs"}:
            continue
        if (
            rel.parts[:2] == ("api", "v1")
            and len(rel.parts) >= 4
            and rel.name == "dto.py"
        ):
            continue
        text = path.read_text(encoding="utf-8")
        updated = apply_imports(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    # --- Update tests & alembic ---
    for root in (BACKEND / "tests", BACKEND / "alembic"):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            updated = apply_imports(text)
            updated = re.sub(r"\.dto\b", ".schemas", updated)
            if updated != text:
                path.write_text(updated, encoding="utf-8")

    # --- Package inits ---
    for pkg in (
        "infrastructure",
        "infrastructure/database",
        "infrastructure/cache",
        "infrastructure/queue",
        "infrastructure/jobs",
        "modules",
        "modules/auth",
        "modules/chat",
        "modules/conversations",
        "modules/knowledge",
    ):
        init = APP / pkg / "__init__.py"
        if not init.exists():
            init.write_text('"""Package."""\n', encoding="utf-8")

    # --- Remove legacy trees ---
    for legacy in ("ai", "db", "models", "services", "clients", "jobs"):
        legacy_path = APP / legacy
        if legacy_path.exists():
            shutil.rmtree(legacy_path)

    for feature in DTO_TO_SCHEMAS:
        dto = APP / f"api/v1/{feature}/dto.py"
        if dto.exists():
            dto.unlink()

    print("Restructure complete.")


if __name__ == "__main__":
    main()
