"""
Metrics and statistics API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus
from app.services.memory_service import get_memory_service
from app.utils.datetime_utils import utcnow

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    # Total agents
    total_agents_result = await db.execute(select(func.count(Agent.id)))
    total_agents = total_agents_result.scalar()

    # Active agents
    active_agents_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.status == AgentStatus.ACTIVE)
    )
    active_agents = active_agents_result.scalar()

    # Total tasks completed
    completed_tasks_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED)
    )
    tasks_completed = completed_tasks_result.scalar()

    # Calculate overall success rate
    all_agents_result = await db.execute(select(Agent))
    all_agents = all_agents_result.scalars().all()

    total_completed = sum(a.tasks_completed for a in all_agents)
    total_failed = sum(a.tasks_failed for a in all_agents)
    total_all = total_completed + total_failed

    avg_success_rate = (total_completed / total_all * 100) if total_all > 0 else 0

    # Weekly trend (mock for now)
    one_week_ago = utcnow() - timedelta(days=7)
    weekly_tasks_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.created_at >= one_week_ago,
            Task.status == TaskStatus.COMPLETED
        )
    )
    weekly_tasks = weekly_tasks_result.scalar()

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "tasks_completed": tasks_completed,
        "avg_success_rate": round(avg_success_rate, 1),
        "trends": {
            "agents_change": "+2 this week",  # Mock
            "tasks_change": f"+{weekly_tasks} from last month",
            "success_rate_change": "+2.3% from last month"  # Mock
        }
    }


@router.get("/agent/{agent_id}")
async def get_agent_metrics(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get metrics for specific agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        return {"error": "Agent not found"}

    # Get task breakdown
    pending_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.agent_id == agent_id,
            Task.status == TaskStatus.PENDING
        )
    )
    pending_tasks = pending_result.scalar()

    running_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.agent_id == agent_id,
            Task.status == TaskStatus.RUNNING
        )
    )
    running_tasks = running_result.scalar()

    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "tasks_completed": agent.tasks_completed,
        "tasks_failed": agent.tasks_failed,
        "success_rate": agent.success_rate,
        "uptime": agent.uptime,
        "last_active": agent.last_active,
        "pending_tasks": pending_tasks,
        "running_tasks": running_tasks,
        "status": agent.status.value
    }


@router.get("/memory")
async def get_memory_statistics():
    """Get memory/storage statistics."""
    memory_service = get_memory_service()
    stats = await memory_service.get_statistics()

    return {
        "memory_statistics": stats,
        "storage_type": "ChromaDB (embedded)"
    }
