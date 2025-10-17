"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.activity import Activity, ActivityBase, ActivityCreate, ActivityList
from app.schemas.agent import (
    Agent,
    AgentBase,
    AgentCreate,
    AgentList,
    AgentStatusUpdate,
    AgentUpdate,
)
from app.schemas.settings import (
    APIKey,
    APIKeyBase,
    APIKeyCreate,
    APIKeyMasked,
    APIKeyUpdate,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.schemas.task import Task, TaskBase, TaskCreate, TaskList, TaskUpdate

__all__ = [
    # Agent schemas
    "AgentBase",
    "AgentCreate",
    "AgentUpdate",
    "AgentStatusUpdate",
    "Agent",
    "AgentList",
    # Task schemas
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "Task",
    "TaskList",
    # Activity schemas
    "ActivityBase",
    "ActivityCreate",
    "Activity",
    "ActivityList",
    # Settings schemas
    "APIKeyBase",
    "APIKeyCreate",
    "APIKeyUpdate",
    "APIKey",
    "APIKeyMasked",
    "ConnectionTestRequest",
    "ConnectionTestResponse",
]
