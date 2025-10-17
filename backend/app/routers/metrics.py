"""
Metrics and statistics API endpoints.
"""

from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus
from app.services.memory_service import get_memory_service
from app.services.trend_calculator import TrendCalculator

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db), current_user: Dict = Depends(get_current_user)
):
    """Get dashboard statistics (requires authentication)."""
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

    # Calculate real trends
    trend_calculator = TrendCalculator()
    agents_trend = await trend_calculator.calculate_agent_trend(db)
    tasks_trend = await trend_calculator.calculate_tasks_trend(db)
    success_rate_trend = await trend_calculator.calculate_success_rate_trend(db)

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "tasks_completed": tasks_completed,
        "avg_success_rate": round(avg_success_rate, 1),
        "trends": {
            "agents_change": agents_trend,
            "tasks_change": tasks_trend,
            "success_rate_change": success_rate_trend,
        },
    }


@router.get("/agent/{agent_id}")
async def get_agent_metrics(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Get metrics for specific agent (requires authentication)."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        return {"error": "Agent not found"}

    # Get task breakdown
    pending_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.agent_id == agent_id, Task.status == TaskStatus.PENDING
        )
    )
    pending_tasks = pending_result.scalar()

    running_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.agent_id == agent_id, Task.status == TaskStatus.RUNNING
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
        "status": agent.status.value,
    }


@router.get("/memory")
async def get_memory_statistics(current_user: Dict = Depends(get_current_user)):
    """Get memory/storage statistics (requires authentication)."""
    memory_service = get_memory_service()
    stats = await memory_service.get_statistics()

    return {"memory_statistics": stats, "storage_type": "ChromaDB (embedded)"}
