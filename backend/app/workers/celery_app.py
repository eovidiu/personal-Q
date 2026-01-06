"""
Celery application configuration.
"""

import asyncio
import logging
import sys

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_init
from config.settings import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "personal_q",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    "cleanup-old-activities": {
        "task": "app.workers.tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "update-agent-metrics": {
        "task": "app.workers.tasks.update_metrics",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}

@worker_init.connect
def init_worker(**kwargs):
    """
    Initialize database when Celery worker starts.

    This ensures the worker has access to all database tables,
    particularly important when running in separate containers
    where SQLite databases are not shared.
    """
    logger.info("Initializing database for Celery worker...")

    # Import here to avoid circular imports
    from app.db.database import init_db

    # Run the async init_db function
    asyncio.run(init_db())

    logger.info("Database initialized for Celery worker")


if __name__ == "__main__":
    celery_app.start()
