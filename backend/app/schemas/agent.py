"""
Pydantic schemas for Agent model with input validation and sanitization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import html
import json
import logging

from app.models.agent import AgentStatus, AgentType

logger = logging.getLogger(__name__)


class AgentBase(BaseModel):
    """Base schema for Agent with validation."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    agent_type: AgentType
    model: str = Field(..., min_length=1, max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=100000)
    system_prompt: str = Field(..., min_length=1, max_length=10000)
    tags: List[str] = Field(default_factory=list)
    avatar_url: Optional[str] = Field(None, max_length=500)
    tools_config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name', 'description')
    @classmethod
    def sanitize_html(cls, v):
        """Escape HTML in text fields to prevent XSS."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt(cls, v):
        """Validate and check system prompt for potential injection."""
        if not v:
            return v
        
        v = v.strip()
        
        # Check for potential prompt injection patterns
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all",
            "new instructions:",
            "forget everything",
            "override your",
            "system: you are now"
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                logger.warning(f"Potential prompt injection pattern detected: '{pattern}'")
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags list."""
        if not v:
            return v
        
        # Limit number of tags
        if len(v) > 20:
            raise ValueError('Too many tags (max 20)')
        
        # Limit tag length and sanitize
        sanitized = []
        for tag in v:
            if not tag or not isinstance(tag, str):
                continue
            tag = tag.strip()[:50]  # Max 50 chars per tag
            if tag:
                sanitized.append(html.escape(tag))
        
        return sanitized[:20]
    
    @field_validator('tools_config')
    @classmethod
    def validate_tools_config(cls, v):
        """Validate size of tools_config."""
        if v is None:
            return v
        # Limit size of tools_config to 10KB
        json_str = json.dumps(v)
        if len(json_str) > 10000:
            raise ValueError('tools_config too large (max 10KB)')
        return v


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
