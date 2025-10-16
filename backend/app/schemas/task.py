"""
Pydantic schemas for Task model with input validation and sanitization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import html
import logging

from app.models.task import TaskStatus, TaskPriority
from app.services.prompt_sanitizer import PromptSanitizer

logger = logging.getLogger(__name__)


class TaskBase(BaseModel):
    """Base schema for Task with validation."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    input_data: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v):
        """Escape HTML in title to prevent XSS."""
        if v:
            return html.escape(v.strip())
        return v

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        """Sanitize task description for LLM safety against prompt injection."""
        if not v:
            return v

        try:
            # Task descriptions go to LLM - MUST sanitize for injection
            sanitized = PromptSanitizer.sanitize(v, max_length=5000)
            return sanitized
        except ValueError as e:
            raise ValueError(f"Task description rejected: {e}")
    
    @field_validator('input_data')
    @classmethod
    def validate_input_data(cls, v):
        """Validate size of input_data to prevent abuse."""
        if v is None:
            return v
        # Limit size of input_data to 10KB
        json_str = json.dumps(v)
        if len(json_str) > 10000:
            raise ValueError('input_data too large (max 10KB)')
        return v


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
