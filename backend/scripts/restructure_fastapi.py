"""
Restructure app/ to FastAPI official layout:

  main.py, dependencies.py, config.py, database.py
  routers/, schemas/, models/, crud/, services/, internal/
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    ("app.api.v1.auth.dto", "app.api.v1.auth.dto"),
    ("app.api.v1.auth.dto", "app.api.v1.auth.dto"),
    ("app.api.v1.chat.dto", "app.api.v1.chat.dto"),
    ("app.api.v1.chat.dto", "app.api.v1.chat.dto"),
    ("app.api.v1.conversations.dto", "app.api.v1.conversations.dto"),
    ("app.api.v1.health.dto", "app.api.v1.health.dto"),
    ("app.api.v1.documents.dto", "app.api.v1.documents.dto"),
    ("app.api.v1.documents.dto", "app.api.v1.documents.dto"),
    ("app.api.v1.auth.router", "app.api.v1.auth.router"),
    ("app.api.v1.chat.router", "app.api.v1.chat.router"),
    ("app.api.v1.conversations.router", "app.api.v1.conversations.router"),
    ("app.api.v1.health.router", "app.api.v1.health.router"),
    ("app.api.v1.documents.router", "app.api.v1.documents.router"),
    ("app.routers", "app.routers"),
    (
        "app.infrastructure.database.repositories.user",
        "app.infrastructure.database.repositories.user",
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
        "app.infrastructure.database.repositories",
        "app.infrastructure.database.repositories",
    ),
    ("app.infrastructure.database.models", "app.infrastructure.database.models"),
    ("app.infrastructure.database.session", "app.infrastructure.database.session"),
    ("app.infrastructure.redis", "app.infrastructure.redis"),
    ("app.ai.providers", "app.ai.providers"),
    ("app.ai.retrieval", "app.ai.retrieval"),
    ("app.infrastructure.external", "app.infrastructure.external"),
    ("app.infrastructure.external", "app.infrastructure.external"),
    ("app.application.auth", "app.application.auth"),
    ("app.application.chat", "app.application.chat"),
    ("app.application.conversations", "app.application.conversations"),
    ("app.application.documents", "app.application.documents"),
    ("app.services", "app.services"),
    ("app.core.dependencies", "app.core.dependencies"),
    ("app.core.config", "app.core.config"),
    ("app.infrastructure.database.session", "app.infrastructure.database.session"),
    ("app.core.middleware", "app.core.middleware"),
    ("app.core.security", "app.core.security"),
    ("app.core.cookies", "app.core.cookies"),
    ("app.core.logging", "app.core.logging"),
    ("app.core.exceptions", "app.core.exceptions"),
    ("app.core.errors", "app.core.errors"),
    ("app.domain", "app.domain"),
]


def move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    shutil.move(str(src), str(dst))


def rewrite_imports(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in IMPORT_REPLACEMENTS:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    # --- Top-level app modules (FastAPI official) ---
    move(APP / "core" / "config.py", APP / "config.py")
    move(APP / "core" / "database.py", APP / "database.py")
    move(APP / "core" / "dependencies.py", APP / "dependencies.py")

    internal = APP / "internal"
    internal.mkdir(exist_ok=True)
    for name in ("middleware", "security", "cookies", "logging", "errors"):
        move(APP / "core" / f"{name}.py", internal / f"{name}.py")
    move(APP / "core" / "exceptions", internal / "exceptions")

    # --- routers/ ---
    routers = APP / "routers"
    routers.mkdir(exist_ok=True)
    for feature in ("auth", "chat", "conversations", "health", "knowledge"):
        move(APP / "api" / "v1" / feature / "router.py", routers / f"{feature}.py")

    # routers/__init__.py from api/v1/router.py
    router_init = (APP / "api" / "v1" / "router.py").read_text(encoding="utf-8")
    router_init = router_init.replace("API v1 router", "API routers aggregator")
    router_init = router_init.replace(
        "from app.api.v1.auth.router import router as auth_router",
        "from app.api.v1.auth.router import router as auth_router",
    )
    router_init = router_init.replace(
        "from app.api.v1.chat.router import router as chat_router",
        "from app.api.v1.chat.router import router as chat_router",
    )
    router_init = router_init.replace(
        "from app.api.v1.conversations.router import router as conversations_router",
        "from app.api.v1.conversations.router import router as conversations_router",
    )
    router_init = router_init.replace(
        "from app.api.v1.health.router import router as health_router",
        "from app.api.v1.health.router import router as health_router",
    )
    router_init = router_init.replace(
        "from app.api.v1.documents.router import router as knowledge_router",
        "from app.api.v1.documents.router import router as knowledge_router",
    )
    (routers / "__init__.py").write_text(router_init, encoding="utf-8")

    # --- schemas/ (was dto/) ---
    schemas = APP / "schemas"
    schemas.mkdir(exist_ok=True)
    for feature in ("auth", "chat", "conversations", "health", "knowledge"):
        dto_dir = APP / "api" / "v1" / feature / "dto"
        if dto_dir.exists():
            move(dto_dir, schemas / feature)

    # --- models/ ---
    move(APP / "infrastructure" / "database" / "models", APP / "models")

    # --- crud/ (was repositories/) ---
    crud = APP / "crud"
    crud.mkdir(exist_ok=True)
    repo_dir = APP / "infrastructure" / "database" / "repositories"
    for repo_file in repo_dir.glob("*.py"):
        if repo_file.name == "__init__.py":
            move(repo_file, crud / "__init__.py")
        elif repo_file.name.endswith("_repository.py"):
            move(repo_file, crud / repo_file.name.replace("_repository", ""))

    move(APP / "infrastructure" / "database" / "session.py", internal / "db_session.py")

    # --- services/ (was application/) ---
    move(APP / "application", APP / "services")

    # --- internal/ adapters ---
    for pkg in ("cache", "llm", "vectorstore", "queue", "jobs"):
        src = APP / "infrastructure" / pkg
        if src.exists():
            move(src, internal / pkg)

    move(APP / "domain", internal / "domain")

    # --- Remove old empty trees ---
    shutil.rmtree(APP / "api", ignore_errors=True)
    shutil.rmtree(APP / "core", ignore_errors=True)
    shutil.rmtree(APP / "infrastructure", ignore_errors=True)

    # --- Fix models/__init__.py load_models imports ---
    models_init = APP / "models" / "__init__.py"
    models_init.write_text(
        '''"""
ORM models package.

Call load_models() before create_all.
"""

from app.infrastructure.database.models.base import Base


def load_models() -> None:
    from app.infrastructure.database.models import (  # noqa: F401
        conversation,
        document,
        message,
        user,
    )


__all__ = ["Base", "load_models"]
''',
        encoding="utf-8",
    )

    # --- Fix model relative imports ---
    for model_file in (APP / "models").glob("*.py"):
        if model_file.name == "__init__.py":
            continue
        text = model_file.read_text(encoding="utf-8")
        text = text.replace(
            "from app.infrastructure.database.models.base",
            "from app.infrastructure.database.models.base",
        )
        model_file.write_text(text, encoding="utf-8")

    # --- crud __init__ ---
    crud_init = APP / "crud" / "__init__.py"
    if crud_init.exists():
        text = crud_init.read_text(encoding="utf-8")
        crud_init.write_text(text, encoding="utf-8")

    # --- internal/__init__.py ---
    (internal / "__init__.py").write_text(
        '"""Non-public implementation details (FastAPI internal/ package)."""\n',
        encoding="utf-8",
    )

    # --- services/__init__ if missing ---
    services_init = APP / "services" / "__init__.py"
    if not services_init.exists():
        services_init.write_text(
            '"""Application use-cases (business logic)."""\n', encoding="utf-8"
        )

    # --- Rewrite imports across backend ---
    for py_file in ROOT.rglob("*.py"):
        if "restructure_fastapi" in str(py_file):
            continue
        if "__pycache__" in str(py_file):
            continue
        rewrite_imports(py_file)

    # --- main.py uses app.routers ---
    main = APP / "main.py"
    text = main.read_text(encoding="utf-8")
    text = text.replace(
        "from app.api.v1.router import api_router",
        "from app.api.v1.router import api_router",
    )
    main.write_text(text, encoding="utf-8")

    # --- database.py SessionLocal used by services ---
    db = APP / "database.py"
    text = db.read_text(encoding="utf-8")
    text = text.replace(
        "from app.infrastructure.database.models",
        "from app.infrastructure.database.models",
    )
    db.write_text(text, encoding="utf-8")

    # --- worker path in docker-compose ---
    compose = ROOT / "docker-compose.yml"
    if compose.exists():
        text = compose.read_text(encoding="utf-8")
        text = text.replace(
            "app.infrastructure.external.worker.WorkerSettings",
            "app.infrastructure.external.worker.WorkerSettings",
        )
        compose.write_text(text, encoding="utf-8")

    print("Restructure complete.")


if __name__ == "__main__":
    main()
