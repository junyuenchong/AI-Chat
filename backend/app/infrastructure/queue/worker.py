"""
ARQ worker settings.

Background job process configuration.
"""

from app.infrastructure.jobs.tasks import process_document, summarize_conversation
from app.infrastructure.queue.queue import redis_settings


# ────────────────────────────────────────────────────────
# WorkerSettings
# Internal — job queue worker
# ARQ worker config: Redis connection and registered background jobs.
# ────────────────────────────────────────────────────────
class WorkerSettings:
    """
    Register background jobs and Redis connection for ARQ.

    Jobs: summarize every N messages; embed after Document create.
    """

    # Redis connection settings shared with the API process.
    redis_settings = redis_settings()
    # Callable tasks the worker process can execute.
    functions = [summarize_conversation, process_document]
    # Cap concurrent jobs so embedding bursts do not overwhelm Postgres.
    max_jobs = 5
