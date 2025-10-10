"""
Schedule model for agent task scheduling.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class Schedule(Base):
    """Schedule model for recurring agent tasks."""

    __tablename__ = "schedules"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Schedule details
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Cron expression for scheduling
    cron_expression = Column(String, nullable=False)
    # Examples: "0 9 * * *" (daily at 9am), "0 * * * *" (hourly)

    # Task configuration
    task_config = Column(JSON, default=dict)  # Input data for the task

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Schedule {self.name} ({self.cron_expression})>"
