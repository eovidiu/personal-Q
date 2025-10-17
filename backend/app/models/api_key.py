"""
ABOUTME: API key storage model for external integrations with encrypted sensitive fields.
ABOUTME: All credentials are encrypted at rest using Fernet symmetric encryption.
"""

from app.db.database import Base
from app.db.encrypted_types import EncryptedString
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func


class APIKey(Base):
    """API key model for storing external service credentials securely."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True)

    # Service identification
    service_name = Column(String, unique=True, nullable=False, index=True)
    # e.g., "anthropic", "slack", "microsoft_graph", "obsidian"

    # Credentials (encrypted at rest)
    api_key = Column(EncryptedString, nullable=True)
    access_token = Column(EncryptedString, nullable=True)
    refresh_token = Column(EncryptedString, nullable=True)
    client_id = Column(String, nullable=True)  # Not sensitive, can be plaintext
    client_secret = Column(EncryptedString, nullable=True)
    tenant_id = Column(String, nullable=True)  # Not sensitive, can be plaintext

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
