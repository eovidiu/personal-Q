"""
ABOUTME: Task API endpoints with rate limiting to control LLM costs.
ABOUTME: Task creation and execution are heavily rate limited.
"""

import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.middleware.rate_limit import get_rate_limit, limiter
from app.models.agent import Agent
from app.models.task import Task as TaskModel
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import Task, TaskCreate, TaskList, TaskUpdate
from app.workers.tasks import execute_agent_task

router = APIRouter()


@router.post("/", response_model=Task, status_code=201)
@limiter.limit(get_rate_limit("task_create"))
async def create_task(
    request: Request,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Create a new task and trigger execution (rate limited, requires authentication)."""
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == task_data.agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create task
    task = TaskModel(id=str(uuid.uuid4()), **task_data.model_dump())

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Trigger async execution
    execute_agent_task.delay(task.id)

    return task


@router.get("/", response_model=TaskList)
@limiter.limit(get_rate_limit("read_operations"))
async def list_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent_id: Optional[str] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """List tasks with filtering and pagination."""
    query = select(TaskModel)

    if agent_id:
        query = query.where(TaskModel.agent_id == agent_id)

    if status:
        query = query.where(TaskModel.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    skip = (page - 1) * page_size
    query = query.order_by(TaskModel.created_at.desc()).offset(skip).limit(page_size)

    result = await db.execute(query)
    tasks = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return TaskList(
        tasks=list(tasks), total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str, db: AsyncSession = Depends(get_db), current_user: Dict = Depends(get_current_user)
):
    """Get task details (requires authentication)."""
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Update task (requires authentication)."""
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return task
