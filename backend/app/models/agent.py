"""
Agent database model.
"""

from sqlalchemy import Column, String, Text, Float, Integer, DateTime, Enum, JSON, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.database import Base


class AgentStatus(str, enum.Enum):
    """Agent status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"
    PAUSED = "paused"


class AgentType(str, enum.Enum):
    """Agent type enum."""
    CONVERSATIONAL = "conversational"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    AUTOMATION = "automation"


class Agent(Base):
    """Agent model representing AI agents in the system."""

    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.INACTIVE, nullable=False)

    # LLM Configuration
    model = Column(String, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    system_prompt = Column(Text, nullable=False)

    # Metadata
    tags = Column(JSON, default=list)  # List of tags
    avatar_url = Column(String, nullable=True)

    # Metrics
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    last_active = Column(DateTime, nullable=True)

    # Capabilities - tool configurations
    tools_config = Column(JSON, default=dict)  # Configuration for enabled tools

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.0
        return (self.tasks_completed / total) * 100

    @property
    def uptime(self) -> float:
        """Calculate uptime percentage (placeholder - will be calculated from activity logs)."""
        # This will be calculated from actual activity tracking
        return 95.0  # Default placeholder

    def __repr__(self):
        return f"<Agent {self.name} ({self.agent_type.value})>"
