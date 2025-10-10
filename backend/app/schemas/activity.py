"""
Pydantic schemas for Activity model.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.activity import ActivityType, ActivityStatus


class ActivityBase(BaseModel):
    """Base schema for Activity."""
    activity_type: ActivityType
    status: ActivityStatus = ActivityStatus.INFO
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    activity_metadata: Dict[str, Any] = Field(default_factory=dict)


class ActivityCreate(ActivityBase):
    """Schema for creating an activity."""
    agent_id: Optional[str] = None
    task_id: Optional[str] = None


class Activity(ActivityBase):
    """Schema for Activity response."""
    id: str
    agent_id: Optional[str]
    task_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityList(BaseModel):
    """Schema for paginated activity list."""
    activities: List[Activity]
    total: int
    page: int
    page_size: int
    total_pages: int
