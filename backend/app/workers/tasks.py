"""
Celery tasks for background processing.
"""

import asyncio
from datetime import timedelta

from app.db.database import AsyncSessionLocal
from app.models.activity import Activity
from app.models.agent import Agent
from app.models.task import Task as TaskModel
from app.models.task import TaskStatus
from app.services.crew_service import CrewService
from app.utils.datetime_utils import utcnow_naive
from app.workers.celery_app import celery_app
from celery import Task
from config.settings import settings
from sqlalchemy import delete, select


class AsyncTask(Task):
    """Base task that supports async operations."""

    def __call__(self, *args, **kwargs):
        """Execute async task."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))

    async def run(self, *args, **kwargs):
        """Override in subclasses."""
        raise NotImplementedError


@celery_app.task(bind=True, base=AsyncTask, name="app.workers.tasks.execute_agent_task")
async def execute_agent_task(self, task_id: str):
    """
    Execute an agent task asynchronously.

    Args:
        task_id: Task ID to execute
    """
    async with AsyncSessionLocal() as db:
        # Get task
        result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        # Get agent
        result = await db.execute(select(Agent).where(Agent.id == task.agent_id))
        agent = result.scalar_one_or_none()

        if not agent:
            task.status = TaskStatus.FAILED
            task.error_message = "Agent not found"
            await db.commit()
            return {"error": "Agent not found"}

        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = utcnow_naive()
        task.celery_task_id = self.request.id
        await db.commit()

        # Broadcast task started event
        from app.routers.websocket import broadcast_event

        await broadcast_event(
            "task_started",
            {
                "task_id": task.id,
                "agent_id": task.agent_id,
                "title": task.title,
                "status": "running",
                "started_at": task.started_at.isoformat(),
            },
        )

        try:
            # Execute with CrewAI
            result = await CrewService.execute_agent_task(
                db, agent, task.description or task.title, task.input_data
            )

            # Update task with result
            task.status = TaskStatus.COMPLETED if result["success"] else TaskStatus.FAILED
            task.output_data = result
            task.completed_at = utcnow_naive()

            if not result["success"]:
                task.error_message = result.get("error", "Unknown error")

            # Calculate execution time
            if task.started_at:
                execution_time = (utcnow_naive() - task.started_at).total_seconds()
                task.execution_time_seconds = int(execution_time)

            # Update agent metrics
            if result["success"]:
                agent.tasks_completed += 1
            else:
                agent.tasks_failed += 1

            agent.last_active = utcnow_naive()

            await db.commit()

            # Broadcast task completion event
            # SECURITY FIX (MEDIUM-009): Sanitize error messages before broadcasting
            from app.utils.security_helpers import classify_error_type, sanitize_error_for_client

            sanitized_error = None
            error_type = None
            if not result["success"] and task.error_message:
                sanitized_error = sanitize_error_for_client(Exception(task.error_message))
                error_type = classify_error_type(Exception(task.error_message))

            event_type = "task_completed" if result["success"] else "task_failed"
            await broadcast_event(
                event_type,
                {
                    "task_id": task.id,
                    "agent_id": task.agent_id,
                    "title": task.title,
                    "status": task.status.value,
                    "output_data": task.output_data,
                    "error_message": sanitized_error,  # Sanitized error message
                    "error_type": error_type,  # Error classification for client handling
                    "execution_time_seconds": task.execution_time_seconds,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                },
            )

            return result

        except Exception as e:
            # Handle execution error
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = utcnow_naive()
            agent.tasks_failed += 1
            await db.commit()

            # SECURITY FIX (MEDIUM-009): Sanitize error before broadcasting to WebSocket
            import logging

            from app.utils.security_helpers import classify_error_type, sanitize_error_for_client

            logger = logging.getLogger(__name__)

            sanitized_error = sanitize_error_for_client(e)
            error_type = classify_error_type(e)

            # Log full error server-side for debugging
            logger.error(f"Task {task.id} failed with exception: {str(e)}", exc_info=True)

            # Broadcast task failure event with sanitized error
            await broadcast_event(
                "task_failed",
                {
                    "task_id": task.id,
                    "agent_id": task.agent_id,
                    "title": task.title,
                    "status": "failed",
                    "error_message": sanitized_error,  # User-friendly sanitized message
                    "error_type": error_type,  # Error classification for client handling
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                },
            )

            return {"success": False, "error": str(e)}


@celery_app.task(name="app.workers.tasks.cleanup_old_data")
def cleanup_old_data():
    """Cleanup old activities and data based on retention policy."""

    async def _cleanup():
        async with AsyncSessionLocal() as db:
            # Calculate cutoff date
            cutoff_date = utcnow_naive() - timedelta(days=settings.memory_retention_days)

            # Delete old activities
            stmt = delete(Activity).where(Activity.created_at < cutoff_date)
            result = await db.execute(stmt)
            deleted_count = result.rowcount

            await db.commit()

            return {"deleted_activities": deleted_count, "cutoff_date": cutoff_date.isoformat()}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_cleanup())


@celery_app.task(name="app.workers.tasks.update_metrics")
def update_metrics():
    """Update agent metrics and statistics."""

    async def _update():
        async with AsyncSessionLocal() as db:
            # Get all agents
            result = await db.execute(select(Agent))
            agents = result.scalars().all()

            updated_count = 0
            for agent in agents:
                # Calculate success rate (already a property, but we could add more metrics)
                # Future: Add uptime calculation, response time averages, etc.
                agent.updated_at = utcnow_naive()
                updated_count += 1

            await db.commit()

            return {"updated_agents": updated_count}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_update())


@celery_app.task(bind=True, name="app.workers.tasks.execute_scheduled_task")
def execute_scheduled_task(self, schedule_id: str):
    """
    Execute a scheduled task.

    Args:
        schedule_id: Schedule ID
    """

    async def _execute():
        async with AsyncSessionLocal() as db:
            from app.models.schedule import Schedule

            # Get schedule
            result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
            schedule = result.scalar_one_or_none()

            if not schedule or not schedule.is_active:
                return {"error": "Schedule not found or inactive"}

            # Create task from schedule
            task = TaskModel(
                id=str(__import__("uuid").uuid4()),
                agent_id=schedule.agent_id,
                title=schedule.name,
                description=schedule.description,
                status=TaskStatus.PENDING,
                input_data=schedule.task_config,
            )
            db.add(task)
            await db.commit()

            # Update schedule last_run
            schedule.last_run = utcnow_naive()
            await db.commit()

            # Execute task asynchronously
            execute_agent_task.delay(task.id)

            return {"task_id": task.id, "schedule_id": schedule_id}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_execute())
