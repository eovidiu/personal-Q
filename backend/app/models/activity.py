"""
Activity log database model.
"""

from sqlalchemy import Column, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class ActivityType(str, enum.Enum):
    """Activity type enum."""
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    INTEGRATION_CONNECTED = "integration_connected"
    INTEGRATION_ERROR = "integration_error"


class ActivityStatus(str, enum.Enum):
    """Activity status/outcome."""
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


class Activity(Base):
    """Activity log model for tracking system events."""

    __tablename__ = "activities"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)

    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False, index=True)
    status = Column(Enum(ActivityStatus), default=ActivityStatus.INFO, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Additional context
    activity_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    agent = relationship("Agent", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.activity_type.value} ({self.status.value})>"
