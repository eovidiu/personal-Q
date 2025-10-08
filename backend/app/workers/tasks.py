"""
Celery tasks for background processing.
"""

from celery import Task
from datetime import datetime, timedelta
from sqlalchemy import select, delete
import sys
import asyncio

sys.path.insert(0, "/root/repo/backend")

from app.workers.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.agent import Agent
from app.models.task import Task as TaskModel, TaskStatus
from app.models.activity import Activity
from app.services.crew_service import CrewService
from config.settings import settings


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
        result = await db.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        # Get agent
        result = await db.execute(
            select(Agent).where(Agent.id == task.agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            task.status = TaskStatus.FAILED
            task.error_message = "Agent not found"
            await db.commit()
            return {"error": "Agent not found"}

        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.celery_task_id = self.request.id
        await db.commit()

        try:
            # Execute with CrewAI
            result = await CrewService.execute_agent_task(
                db,
                agent,
                task.description or task.title,
                task.input_data
            )

            # Update task with result
            task.status = TaskStatus.COMPLETED if result["success"] else TaskStatus.FAILED
            task.output_data = result
            task.completed_at = datetime.utcnow()

            if not result["success"]:
                task.error_message = result.get("error", "Unknown error")

            # Calculate execution time
            if task.started_at:
                execution_time = (datetime.utcnow() - task.started_at).total_seconds()
                task.execution_time_seconds = int(execution_time)

            # Update agent metrics
            if result["success"]:
                agent.tasks_completed += 1
            else:
                agent.tasks_failed += 1

            agent.last_active = datetime.utcnow()

            await db.commit()

            return result

        except Exception as e:
            # Handle execution error
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            agent.tasks_failed += 1
            await db.commit()

            return {"success": False, "error": str(e)}


@celery_app.task(name="app.workers.tasks.cleanup_old_data")
def cleanup_old_data():
    """Cleanup old activities and data based on retention policy."""

    async def _cleanup():
        async with AsyncSessionLocal() as db:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=settings.memory_retention_days)

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
                agent.updated_at = datetime.utcnow()
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
            result = await db.execute(
                select(Schedule).where(Schedule.id == schedule_id)
            )
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
                input_data=schedule.task_config
            )
            db.add(task)
            await db.commit()

            # Update schedule last_run
            schedule.last_run = datetime.utcnow()
            await db.commit()

            # Execute task asynchronously
            execute_agent_task.delay(task.id)

            return {"task_id": task.id, "schedule_id": schedule_id}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_execute())
