# Restructure app/ to target clean-architecture layout
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$APP = Join-Path $ROOT "app"

function Move-FileSafe($src, $dst) {
    if (-not (Test-Path $src)) { return }
    $dir = Split-Path $dst -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
    Move-Item $src $dst -Force
}

# core
Move-FileSafe (Join-Path $APP "config.py") (Join-Path $APP "core\config.py")
Move-FileSafe (Join-Path $APP "dependencies.py") (Join-Path $APP "core\dependencies.py")
Move-FileSafe (Join-Path $APP "internal\security.py") (Join-Path $APP "core\security.py")
Move-FileSafe (Join-Path $APP "internal\cookies.py") (Join-Path $APP "core\cookies.py")
Move-FileSafe (Join-Path $APP "internal\logging.py") (Join-Path $APP "core\logging.py")
Move-FileSafe (Join-Path $APP "internal\middleware.py") (Join-Path $APP "core\middleware.py")
Move-FileSafe (Join-Path $APP "internal\errors.py") (Join-Path $APP "core\errors.py")
Move-FileSafe (Join-Path $APP "internal\exceptions") (Join-Path $APP "core\exceptions")

# infrastructure database
Move-FileSafe (Join-Path $APP "database.py") (Join-Path $APP "infrastructure\database\session.py")
Move-FileSafe (Join-Path $APP "models") (Join-Path $APP "infrastructure\database\models")
Move-FileSafe (Join-Path $APP "crud") (Join-Path $APP "infrastructure\database\repositories")

# redis
Move-FileSafe (Join-Path $APP "internal\cache\redis.py") (Join-Path $APP "infrastructure\redis\client.py")
Move-FileSafe (Join-Path $APP "internal\cache\session.py") (Join-Path $APP "infrastructure\redis\session.py")

# external
Move-FileSafe (Join-Path $APP "internal\queue\queue.py") (Join-Path $APP "infrastructure\external\queue.py")
Move-FileSafe (Join-Path $APP "internal\queue\worker.py") (Join-Path $APP "infrastructure\external\worker.py")
Move-FileSafe (Join-Path $APP "internal\jobs\tasks.py") (Join-Path $APP "infrastructure\external\tasks.py")

# ai
Move-FileSafe (Join-Path $APP "internal\llm") (Join-Path $APP "ai\providers")
Move-FileSafe (Join-Path $APP "internal\vectorstore\embeddings.py") (Join-Path $APP "ai\providers\embeddings.py")
Move-FileSafe (Join-Path $APP "internal\vectorstore\retriever.py") (Join-Path $APP "ai\retrieval\retriever.py")
Move-FileSafe (Join-Path $APP "internal\vectorstore\retrieval_strategies.py") (Join-Path $APP "ai\retrieval\strategies.py")
Move-FileSafe (Join-Path $APP "ai\providers\langchain_rag.py") (Join-Path $APP "ai\retrieval\adapter.py")
Move-FileSafe (Join-Path $APP "ai\providers\factory.py") (Join-Path $APP "ai\providers\llm.py")
Move-FileSafe (Join-Path $APP "ai\providers\provider_registry.py") (Join-Path $APP "ai\providers\registry.py")

# domain
Move-FileSafe (Join-Path $APP "internal\domain\chat") (Join-Path $APP "domain\chat")
@("auth","conversations","documents") | ForEach-Object {
    $d = Join-Path $APP "domain\$_"
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    $init = Join-Path $d "__init__.py"
    if (-not (Test-Path $init)) { Set-Content $init "`"``"Domain layer — $_.`"``""`n" }
}

# application
Move-FileSafe (Join-Path $APP "services\auth") (Join-Path $APP "application\auth")
Move-FileSafe (Join-Path $APP "services\chat") (Join-Path $APP "application\chat")
Move-FileSafe (Join-Path $APP "services\conversations") (Join-Path $APP "application\conversations")
Move-FileSafe (Join-Path $APP "services\knowledge") (Join-Path $APP "application\documents")

# prompts split + chains
$prompts = Join-Path $APP "application\chat\prompts.py"
if (Test-Path $prompts) {
    $text = Get-Content $prompts -Raw
    $chatDir = Join-Path $APP "ai\prompts"
    New-Item -ItemType Directory -Path $chatDir -Force | Out-Null
    # write chat.py and summarize.py via python-less regex in PS
    $chatOut = @'
"""Chat prompts — system prompt and RAG context helpers."""

'@ + ($text -replace '(?s)SUMMARIZE_SYSTEM_PROMPT.*?SUMMARIZE_USER_PROMPT = \([^)]+\)\s*', '')
    Set-Content (Join-Path $chatDir "chat.py") $chatOut.TrimEnd()
    $sumOut = @'
"""Summarize prompts for conversation summary jobs."""

SUMMARIZE_SYSTEM_PROMPT = "You write short conversation summaries for a chat database."

SUMMARIZE_USER_PROMPT = (
    "Summarize this chat in 2-4 sentences. "
    "Keep user intent, decisions, and any follow-ups.\n\n{transcript}"
)
'@
    Set-Content (Join-Path $chatDir "summarize.py") $sumOut
    Remove-Item $prompts
}
Move-FileSafe (Join-Path $APP "application\chat\helpers.py") (Join-Path $APP "ai\chains\chat.py")

# api routers
@{
    auth = "auth.py"; chat = "chat.py"; conversations = "conversations.py"
    documents = "knowledge.py"; health = "health.py"
} | ForEach-Object { }  # placeholder

Move-FileSafe (Join-Path $APP "routers\auth.py") (Join-Path $APP "api\v1\auth\router.py")
Move-FileSafe (Join-Path $APP "routers\chat.py") (Join-Path $APP "api\v1\chat\router.py")
Move-FileSafe (Join-Path $APP "routers\conversations.py") (Join-Path $APP "api\v1\conversations\router.py")
Move-FileSafe (Join-Path $APP "routers\knowledge.py") (Join-Path $APP "api\v1\documents\router.py")
Move-FileSafe (Join-Path $APP "routers\health.py") (Join-Path $APP "api\v1\health\router.py")

# router.py
$routerInit = Join-Path $APP "routers\__init__.py"
if (Test-Path $routerInit) {
    $rt = Get-Content $routerInit -Raw
    $rt = $rt -replace 'app\.routers\.knowledge', 'app.api.v1.documents.router'
    $rt = $rt -replace 'app\.routers\.(\w+)', 'app.api.v1.$1.router'
    $rt = $rt -replace 'knowledge_router', 'documents_router'
    $dst = Join-Path $APP "api\v1\router.py"
    New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
    Set-Content $dst $rt
}

# pgvector stub
$pg = Join-Path $APP "infrastructure\vectorstore\pgvector.py"
New-Item -ItemType Directory -Path (Split-Path $pg) -Force | Out-Null
if (-not (Test-Path $pg)) {
    Set-Content $pg '"""pgvector storage helpers."""' 
}

Write-Host "File moves done. Run import rewrite next."
