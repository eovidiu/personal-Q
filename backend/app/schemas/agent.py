"""
Pydantic schemas for Agent model.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys

sys.path.insert(0, "/root/repo/backend")

from app.models.agent import AgentStatus, AgentType


class AgentBase(BaseModel):
    """Base schema for Agent."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    agent_type: AgentType
    model: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=100000)
    system_prompt: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    avatar_url: Optional[str] = None
    tools_config: Dict[str, Any] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    agent_type: Optional[AgentType] = None
    model: Optional[str] = Field(None, min_length=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    system_prompt: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    tools_config: Optional[Dict[str, Any]] = None


class AgentStatusUpdate(BaseModel):
    """Schema for updating agent status."""
    status: AgentStatus


class Agent(AgentBase):
    """Schema for Agent response."""
    id: str
    status: AgentStatus
    tasks_completed: int
    tasks_failed: int
    last_active: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    success_rate: float
    uptime: float

    class Config:
        from_attributes = True


class AgentList(BaseModel):
    """Schema for paginated agent list."""
    agents: List[Agent]
    total: int
    page: int
    page_size: int
    total_pages: int
