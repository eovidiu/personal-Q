"""
Settings and API key management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from typing import Dict

from app.db.database import get_db
from app.schemas.settings import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyMasked,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.models.api_key import APIKey
from app.services.llm_service import get_llm_service
from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api-keys", response_model=list[APIKeyMasked])
async def list_api_keys(
    db: AsyncSession = Depends(get_db), current_user: Dict = Depends(get_current_user)
):
    """List all API keys (masked, requires authentication)."""
    result = await db.execute(select(APIKey))
    api_keys = result.scalars().all()

    return [APIKeyMasked.from_api_key(key) for key in api_keys]


@router.post("/api-keys", response_model=APIKeyMasked, status_code=201)
async def create_or_update_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Create or update an API key (requires authentication)."""
    # Check if key exists
    result = await db.execute(select(APIKey).where(APIKey.service_name == key_data.service_name))
    existing_key = result.scalar_one_or_none()

    if existing_key:
        # Update existing
        for field, value in key_data.model_dump(exclude_unset=True).items():
            if field != "service_name":
                setattr(existing_key, field, value)
        api_key = existing_key
    else:
        # Create new
        api_key = APIKey(id=str(uuid.uuid4()), **key_data.model_dump())
        db.add(api_key)

    await db.commit()
    await db.refresh(api_key)

    return APIKeyMasked.from_api_key(api_key)


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    test_data: ConnectionTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Test API connection for a service (requires authentication)."""
    # Get API key
    result = await db.execute(select(APIKey).where(APIKey.service_name == test_data.service_name))
    api_key = result.scalar_one_or_none()

    if not api_key:
        return ConnectionTestResponse(
            service_name=test_data.service_name, success=False, message="API key not configured"
        )

    # Test based on service
    if test_data.service_name == "anthropic":
        llm_service = get_llm_service()
        try:
            is_valid = await llm_service.validate_api_key(api_key.api_key)
            return ConnectionTestResponse(
                service_name=test_data.service_name,
                success=is_valid,
                message="Connection successful" if is_valid else "Invalid API key",
            )
        except Exception as e:
            # Log full error but don't expose to user
            logger.error(f"Connection test failed for {test_data.service_name}: {e}", exc_info=True)
            return ConnectionTestResponse(
                service_name=test_data.service_name,
                success=False,
                message="Connection failed. Please check your API key and try again.",
            )

    # For other services, return placeholder
    return ConnectionTestResponse(
        service_name=test_data.service_name,
        success=True,
        message="Connection test not implemented for this service",
    )


@router.delete("/api-keys/{service_name}", status_code=204)
async def delete_api_key(
    service_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Delete an API key (requires authentication)."""
    result = await db.execute(select(APIKey).where(APIKey.service_name == service_name))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(api_key)
    await db.commit()

    return None
