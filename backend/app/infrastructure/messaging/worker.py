"""
ARQ worker settings.

Background job process configuration.
"""

from app.infrastructure.messaging.queue import redis_settings
from app.infrastructure.messaging.tasks import process_document, summarize_conversation


# ────────────────────────────────────────────────────────
# WorkerSettings
# Internal — messaging worker
# ARQ worker config: Redis connection and registered background jobs.
# ────────────────────────────────────────────────────────
class WorkerSettings:
    """
    Register background jobs and Redis connection for ARQ.

    Jobs: summarize every N messages; embed after Document create.
    Retries transient failures up to max_tries before marking the job failed.
    """

    redis_settings = redis_settings()
    functions = [summarize_conversation, process_document]
    max_jobs = 5
    max_tries = 3
    retry_jobs = True
