"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.agent import (
    AgentBase,
    AgentCreate,
    AgentUpdate,
    AgentStatusUpdate,
    Agent,
    AgentList,
)
from app.schemas.task import TaskBase, TaskCreate, TaskUpdate, Task, TaskList
from app.schemas.activity import ActivityBase, ActivityCreate, Activity, ActivityList
from app.schemas.settings import (
    APIKeyBase,
    APIKeyCreate,
    APIKeyUpdate,
    APIKey,
    APIKeyMasked,
    ConnectionTestRequest,
    ConnectionTestResponse,
)

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
