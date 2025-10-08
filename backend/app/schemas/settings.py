"""
Pydantic schemas for Settings/API Keys.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class APIKeyBase(BaseModel):
    """Base schema for API Key."""
    service_name: str = Field(..., min_length=1, max_length=100)
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    config: Optional[str] = None
    is_active: bool = True


class APIKeyCreate(APIKeyBase):
    """Schema for creating/updating an API key."""
    pass


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    config: Optional[str] = None
    is_active: Optional[bool] = None


class APIKey(APIKeyBase):
    """Schema for API Key response (masked)."""
    id: str
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyMasked(BaseModel):
    """Schema for masked API key display."""
    id: str
    service_name: str
    is_active: bool
    has_api_key: bool
    has_access_token: bool
    has_client_credentials: bool
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_api_key(cls, api_key: APIKey):
        """Create masked version from full API key."""
        return cls(
            id=api_key.id,
            service_name=api_key.service_name,
            is_active=api_key.is_active,
            has_api_key=bool(api_key.api_key),
            has_access_token=bool(api_key.access_token),
            has_client_credentials=bool(api_key.client_id and api_key.client_secret),
            last_validated=api_key.last_validated,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )


class ConnectionTestRequest(BaseModel):
    """Schema for testing connection."""
    service_name: str


class ConnectionTestResponse(BaseModel):
    """Schema for connection test result."""
    service_name: str
    success: bool
    message: str
