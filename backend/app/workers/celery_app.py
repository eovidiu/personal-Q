"""
Celery application configuration.
"""

import sys

from celery import Celery
from celery.schedules import crontab
from config.settings import settings

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
