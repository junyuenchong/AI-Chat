"""Migrate to api/dto + application + domain + infrastructure layout."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

IMPORT_REPLACEMENTS = [
    (r"\bapp\.modules\.chat\b", "app.application.chat"),
    (r"\bapp\.modules\.auth\b", "app.application.auth"),
    (r"\bapp\.modules\.conversations\b", "app.application.conversations"),
    (r"\bapp\.modules\.knowledge\b", "app.application.documents"),
    (r"\bapp\.api\.v1\.auth\.mapping\b", "app.application.auth.mapper"),
    (r"\bapp\.api\.v1\.chat\.mapping\b", "app.application.chat.mapper"),
    (
        r"\bapp\.api\.v1\.conversations\.mapping\b",
        "app.application.conversations.mapper",
    ),
    (r"\bapp\.api\.v1\.knowledge\.mapping\b", "app.application.documents.mapper"),
    (
        r"\bapp\.infrastructure\.database\.session\b",
        "app.infrastructure.database.session",
    ),
    (
        r"\bapp\.modules\.conversations\.repository\b",
        "app.infrastructure.database.repositories.chat_repository",
    ),
    (
        r"\bapp\.modules\.auth\.repository\b",
        "app.infrastructure.database.repositories.user",
    ),
    (
        r"\bapp\.modules\.knowledge\.repository\b",
        "app.infrastructure.database.repositories.document",
    ),
    (
        r"\bapp\.infrastructure\.ai\.langchain\b",
        "app.infrastructure.ai.langchain_provider",
    ),
    (r"\bapp\.infrastructure\.ai\.llm\b", "app.infrastructure.ai.langchain_provider"),
    (
        r"\bapp\.application\.chat\.providers\b",
        "app.infrastructure.ai.langchain_provider",
    ),
    (r"\bapp\.api\.v1\.auth\.schemas\b", "app.api.v1.auth.dto"),
    (r"\bapp\.api\.v1\.chat\.schemas\b", "app.api.v1.chat.dto"),
    (r"\bapp\.api\.v1\.conversations\.schemas\b", "app.api.v1.conversations.dto"),
    (r"\bapp\.api\.v1\.knowledge\.schemas\b", "app.api.v1.knowledge.dto"),
    (r"\bapp\.api\.v1\.health\.schemas\b", "app.api.v1.health.dto"),
]

DTO_SPLITS: dict[str, dict[str, list[str]]] = {
    "auth": {
        "request": ["RegisterRequest", "LoginRequest"],
        "response": ["TokenResponse", "UserResponse"],
    },
    "chat": {
        "request": ["ChatRequest"],
        "response": ["ChatCompleteResponse"],
    },
    "conversations": {
        "request": [],
        "response": [
            "MessageResponse",
            "ConversationResponse",
            "ConversationDetailResponse",
        ],
    },
    "knowledge": {
        "request": ["CreateDocumentRequest"],
        "response": ["DocumentResponse"],
    },
    "health": {
        "request": [],
        "response": ["HealthLayersResponse", "HealthResponse"],
    },
}


def apply_imports(content: str) -> str:
    for pattern, repl in IMPORT_REPLACEMENTS:
        content = re.sub(pattern, repl, content)
    # dto package imports — map class names to request/response modules
    for feature, split in DTO_SPLITS.items():
        for cls in split["request"]:
            content = re.sub(
                rf"from app\.api\.v1\.{feature}\.dto import ([^;\n]*)",
                lambda m, c=cls, f=feature: (
                    f"from app.api.v1.{f}.dto.request import {m.group(1)}"
                    if c in m.group(1)
                    else m.group(0)
                ),
                content,
            )
            content = content.replace(
                f"from app.api.v1.{feature}.dto import {cls}",
                f"from app.api.v1.{feature}.dto.request import {cls}",
            )
        for cls in split["response"]:
            content = content.replace(
                f"from app.api.v1.{feature}.dto import {cls}",
                f"from app.api.v1.{feature}.dto.response import {cls}",
            )
        # Combined imports like "from app.api.v1.auth.dto import A, B"
        content = re.sub(
            rf"from app\.api\.v1\.{feature}\.dto import (.+)",
            lambda m, f=feature, s=split: _split_dto_import(f, m.group(1)),
            content,
        )
    content = content.replace("AuthMapper", "AuthMapper").replace(
        "from app.application.auth.mapper import AuthMapper",
        "from app.application.auth.mapper import AuthMapper",
    )
    return content


def _split_dto_import(feature: str, names: str) -> str:
    parts = [n.strip() for n in names.split(",")]
    req = [p for p in parts if p in DTO_SPLITS[feature]["request"]]
    res = [p for p in parts if p in DTO_SPLITS[feature]["response"]]
    lines = []
    if req:
        lines.append(f"from app.api.v1.{feature}.dto.request import {', '.join(req)}")
    if res:
        lines.append(f"from app.api.v1.{feature}.dto.response import {', '.join(res)}")
    return (
        "\n".join(lines) if lines else f"from app.api.v1.{feature}.dto import {names}"
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(apply_imports(content), encoding="utf-8")


def copy_transform(src: Path, dst: Path) -> None:
    if src.exists():
        write(dst, src.read_text(encoding="utf-8"))


def split_schemas(feature: str) -> None:
    src = APP / f"api/v1/{feature}/schemas.py"
    if not src.exists():
        return
    text = src.read_text(encoding="utf-8")
    split = DTO_SPLITS[feature]
    req_names = set(split["request"])
    res_names = set(split["response"])

    blocks = _extract_classes(text)
    header = '"""API DTOs."""\n\n'
    shared_imports = _extract_imports(text)

    req_body = shared_imports + "\n\n" if req_names else ""
    res_body = shared_imports + "\n\n" if res_names else ""
    for name, body in blocks:
        if name in req_names:
            req_body += body + "\n\n"
        elif name in res_names:
            res_body += body + "\n\n"

    if req_names:
        write(
            APP / f"api/v1/{feature}/dto/request.py",
            f'"""{feature.title()} request DTOs."""\n\n{req_body.strip()}\n',
        )
        write(APP / f"api/v1/{feature}/dto/__init__.py", '"""DTO package."""\n')
    if res_names:
        write(
            APP / f"api/v1/{feature}/dto/response.py",
            f'"""{feature.title()} response DTOs."""\n\n{res_body.strip()}\n',
        )
        if not req_names:
            write(APP / f"api/v1/{feature}/dto/__init__.py", '"""DTO package."""\n')


def _extract_imports(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("from ") or line.startswith("import "):
            if '"""' not in line:
                lines.append(line)
        elif line.strip() and not line.startswith('"""') and "class " not in line:
            if lines:
                break
    return "\n".join(lines)


def _extract_classes(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"^class (\w+)\(", re.MULTILINE)
    matches = list(pattern.finditer(text))
    result = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result.append((match.group(1), text[start:end].rstrip()))
    return result


def merge_langchain_provider() -> str:
    llm = (APP / "infrastructure/ai/llm.py").read_text(encoding="utf-8")
    lc = (APP / "infrastructure/ai/langchain.py").read_text(encoding="utf-8")
    providers = (APP / "modules/chat/providers.py").read_text(encoding="utf-8")
    providers = providers.replace(
        "from app.infrastructure.ai.langchain import build_lc_messages, chunk_text\n"
        "from app.infrastructure.ai.llm import get_chat_model\n"
        "from app.modules.chat.prompts import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT\n",
        "from app.ai.prompts.chat import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_PROMPT\n",
    )
    providers = providers.replace("app.modules.chat.prompts", "app.ai.prompts.chat")
    body = (
        '"""LangChain LLM provider — factory, messages, stream, complete, summarize."""\n\n'
        + llm.split("\n", 1)[1].strip()
        + "\n\n\n"
        + lc.split("\n", 1)[1].strip()
        + "\n\n\n"
        + providers.split("\n", 1)[1].strip()
        + "\n"
    )
    body = body.replace(
        "from app.modules.chat.prompts import SYSTEM_PROMPT, with_rag_context",
        "from app.ai.prompts.chat import SYSTEM_PROMPT, with_rag_context",
    )
    return body


def create_domain_chat() -> None:
    write(
        APP / "domain/chat/entities.py",
        '''"""Chat domain types."""

from typing import TypedDict


class ChatResult(TypedDict, total=False):
    """Result of a non-streaming chat turn."""

    route: str
    rag_context: str | None
    answer: str
''',
    )
    write(
        APP / "domain/chat/ports.py",
        '''"""Chat domain ports (implemented by infrastructure)."""

from collections.abc import AsyncIterator
from typing import Protocol


class LLMProviderPort(Protocol):
    async def stream_reply(
        self,
        history: list[tuple[str, str]],
        user_message: str,
        rag_context: str | None = None,
    ) -> AsyncIterator[str]: ...

    async def complete_reply(
        self,
        history: list[tuple[str, str]],
        user_message: str,
        rag_context: str | None = None,
    ) -> str: ...
''',
    )
    for pkg in ("domain", "domain/chat"):
        init = APP / pkg / "__init__.py"
        if not init.exists():
            init.write_text('"""Package."""\n', encoding="utf-8")


def strip_chat_result_from_service(content: str) -> str:
    content = content.replace(
        "class ChatResult(TypedDict, total=False):\n"
        '    """Result of a non-streaming chat turn."""\n\n'
        "    route: str\n"
        "    rag_context: str | None\n"
        "    answer: str\n\n\n",
        "",
    )
    content = content.replace("from typing import TypedDict\n\n", "")
    if (
        "ChatResult" in content
        and "from app.domain.chat.entities import ChatResult" not in content
    ):
        content = content.replace(
            "from sqlalchemy.ext.asyncio import AsyncSession\n",
            "from sqlalchemy.ext.asyncio import AsyncSession\n\nfrom app.domain.chat.entities import ChatResult\n",
        )
    content = content.replace(
        "from app.application.chat.providers import complete_reply, stream_reply\n",
        "from app.infrastructure.ai.langchain_provider import complete_reply, stream_reply\n",
    )
    content = content.replace(
        "from app.application.documents.retriever import retrieve_context\n",
        "from app.infrastructure.knowledge.retriever import retrieve_context\n",
    )
    content = content.replace(
        "from app.api.v1.chat.dto import ChatCompleteResponse, ChatRequest\n",
        "from app.api.v1.chat.dto import ChatRequest\n"
        "from app.api.v1.chat.dto import ChatCompleteResponse\n",
    )
    content = content.replace(
        "from app.api.v1.chat.schemas import ChatCompleteResponse, ChatRequest\n",
        "from app.api.v1.chat.dto import ChatRequest\n"
        "from app.api.v1.chat.dto import ChatCompleteResponse\n",
    )
    return content


def main() -> None:
    # --- DTO split ---
    for feature in DTO_SPLITS:
        split_schemas(feature)

    # --- core/database.py from infrastructure/database/session.py ---
    copy_transform(APP / "infrastructure/database/session.py", APP / "core/database.py")

    # --- infrastructure: repositories ---
    copy_transform(
        APP / "modules/conversations/repository.py",
        APP / "infrastructure/database/repositories/chat_repository.py",
    )
    copy_transform(
        APP / "modules/auth/repository.py",
        APP / "infrastructure/database/repositories/user_repository.py",
    )
    copy_transform(
        APP / "modules/knowledge/repository.py",
        APP / "infrastructure/database/repositories/document_repository.py",
    )
    write(
        APP / "infrastructure/database/repositories/__init__.py",
        '"""SQLAlchemy repositories."""\n',
    )

    # --- infrastructure: knowledge retriever/embeddings ---
    copy_transform(
        APP / "modules/knowledge/retriever.py",
        APP / "infrastructure/knowledge/retriever.py",
    )
    copy_transform(
        APP / "modules/knowledge/embeddings.py",
        APP / "infrastructure/knowledge/embeddings.py",
    )
    write(
        APP / "infrastructure/knowledge/__init__.py",
        '"""Knowledge infrastructure."""\n',
    )

    # --- infrastructure: langchain provider ---
    write(APP / "infrastructure/ai/langchain_provider.py", merge_langchain_provider())

    # --- application layer ---
    for name in ("auth", "chat", "conversations", "knowledge"):
        copy_transform(
            APP / f"modules/{name}/service.py", APP / f"application/{name}/service.py"
        )
        mapping = APP / f"api/v1/{name}/mapping.py"
        if mapping.exists():
            write(
                APP / f"application/{name}/mapper.py",
                mapping.read_text(encoding="utf-8"),
            )

    copy_transform(APP / "modules/chat/prompts.py", APP / "application/chat/prompts.py")

    # --- chat service cleanup ---
    chat_svc = APP / "application/chat/service.py"
    if chat_svc.exists():
        write(
            APP / "application/chat/service.py",
            strip_chat_result_from_service(chat_svc.read_text(encoding="utf-8")),
        )

    create_domain_chat()

    # --- session shim for backwards compat during import sweep ---
    write(
        APP / "infrastructure/database/session.py",
        '"""Deprecated — use app.infrastructure.database.session."""\n\nfrom app.infrastructure.database.session import *  # noqa: F403\n',
    )

    # --- sweep imports ---
    for path in list(APP.rglob("*.py")):
        rel = path.relative_to(APP)
        if rel.parts[0] in {"modules"}:
            continue
        if rel.parts[:3] == ("api", "v1", "health") and rel.name == "schemas.py":
            continue
        if (
            len(rel.parts) >= 4
            and rel.parts[2] != "dto"
            and rel.name in {"schemas.py", "mapping.py"}
        ):
            if rel.parts[1] == "v1" and rel.parts[2] in DTO_SPLITS:
                continue
        text = path.read_text(encoding="utf-8")
        updated = apply_imports(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    for root in (BACKEND / "tests", BACKEND / "alembic"):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            updated = apply_imports(text)
            updated = updated.replace(".schemas", ".dto")
            updated = re.sub(
                r"from app\.api\.v1\.(\w+)\.dto import (.+)",
                lambda m: _split_dto_import(m.group(1), m.group(2)),
                updated,
            )
            if updated != text:
                path.write_text(updated, encoding="utf-8")

    # --- package inits ---
    for pkg in (
        "application",
        "application/auth",
        "application/chat",
        "application/conversations",
        "application/knowledge",
    ):
        init = APP / pkg / "__init__.py"
        if not init.exists():
            init.write_text('"""Application use-cases."""\n', encoding="utf-8")

    # --- remove legacy ---
    if (APP / "modules").exists():
        shutil.rmtree(APP / "modules")
    for feature in DTO_SPLITS:
        for legacy in ("schemas.py", "mapping.py"):
            p = APP / f"api/v1/{feature}/{legacy}"
            if p.exists():
                p.unlink()
    for legacy in ("infrastructure/ai/langchain.py", "infrastructure/ai/llm.py"):
        p = APP / legacy
        if p.exists():
            p.unlink()

    print("Clean architecture restructure complete.")


if __name__ == "__main__":
    main()
