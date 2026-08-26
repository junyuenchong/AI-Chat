"""ARQ worker process settings — docker: arq app.jobs.worker.WorkerSettings."""

from app.clients.queue import redis_settings
from app.jobs.tasks import process_document, summarize_conversation


class WorkerSettings:
    """Register background jobs and Redis connection for ARQ."""

    redis_settings = redis_settings()
    # ---------------------------------------------------------------------------
    # Jobs — summarize every N messages; embed after Document create.
    # ---------------------------------------------------------------------------
    functions = [summarize_conversation, process_document]
    max_jobs = 5
