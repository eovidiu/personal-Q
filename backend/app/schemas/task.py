"""
Pydantic schemas for Task model.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys

sys.path.insert(0, "/root/repo/backend")

from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base schema for Task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    input_data: Dict[str, Any] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    agent_id: str


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None


class Task(TaskBase):
    """Schema for Task response."""
    id: str
    agent_id: str
    status: TaskStatus
    priority: TaskPriority
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    celery_task_id: Optional[str]
    execution_time_seconds: Optional[int]
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskList(BaseModel):
    """Schema for paginated task list."""
    tasks: List[Task]
    total: int
    page: int
    page_size: int
    total_pages: int
