"""
API key storage model for external integrations.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from app.db.database import Base


class APIKey(Base):
    """API key model for storing external service credentials."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True)

    # Service identification
    service_name = Column(String, unique=True, nullable=False, index=True)
    # e.g., "anthropic", "slack", "microsoft_graph", "obsidian"

    # Credentials (stored as plain text per requirements)
    api_key = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    client_id = Column(String, nullable=True)
    client_secret = Column(Text, nullable=True)
    tenant_id = Column(String, nullable=True)

    # Configuration
    config = Column(Text, nullable=True)  # JSON string for additional config

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_validated = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<APIKey {self.service_name}>"
