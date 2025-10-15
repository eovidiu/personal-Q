"""
Task database model.
"""

from sqlalchemy import Column, String, Text, DateTime, Enum, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class TaskStatus(str, enum.Enum):
    """Task status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """Task model representing work items for agents."""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(
        String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Task details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)

    # Execution details
    input_data = Column(JSON, default=dict)  # Input parameters for the task
    output_data = Column(JSON, nullable=True)  # Task results
    error_message = Column(Text, nullable=True)

    # Celery task tracking
    celery_task_id = Column(String, nullable=True, index=True)

    # Metrics
    execution_time_seconds = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.title} ({self.status.value})>"
