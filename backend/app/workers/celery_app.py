"""
Celery application configuration.
"""

import logging

from celery import Celery
from celery.schedules import crontab
from config.settings import settings

logger = logging.getLogger(__name__)


def _init_database_sync():
    """
    Initialize database tables synchronously.
    Called at module load time to ensure tables exist before any tasks run.
    """
    try:
        from app.db.database import Base
        from app.models import Agent, Task, Activity, APIKey, Schedule  # noqa: F401 - Import to register models

        import sqlalchemy

        # Determine sync URL based on database type
        db_url = settings.database_url

        if db_url.startswith("sqlite"):
            # SQLite: already in sync format
            sync_url = db_url
            engine_args = {"connect_args": {"check_same_thread": False}}
        elif db_url.startswith("postgresql"):
            # PostgreSQL: use psycopg2 sync driver (already default for postgresql://)
            sync_url = db_url
            engine_args = {}
        else:
            logger.error(f"Unsupported database URL scheme: {db_url}")
            return

        sync_engine = sqlalchemy.create_engine(sync_url, **engine_args)
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


# Initialize database at module load time
_init_database_sync()

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

if __name__ == "__main__":
    celery_app.start()
