"""
Settings and API key management endpoints.
"""

import logging
import uuid
from typing import Dict

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.middleware.rate_limit import get_rate_limit, limiter
from app.models.api_key import APIKey
from app.schemas.settings import (
    APIKeyCreate,
    APIKeyMasked,
    APIKeyUpdate,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.services.llm_service import get_llm_service
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api-key-status")
async def get_api_key_status(
    request: Request,
    current_user: Dict = Depends(get_current_user),
):
    """
    Get API key configuration status.

    Returns whether PERSONAL_Q_API_KEY environment variable is set.
    """
    from config.settings import settings

    if settings.personal_q_api_key:
        return {
            "configured": True,
            "variable_name": "PERSONAL_Q_API_KEY",
            "message": "API key configured via environment variable",
        }

    return {
        "configured": False,
        "message": "PERSONAL_Q_API_KEY environment variable is not set.",
    }


@router.get("/api-keys", response_model=list[APIKeyMasked])
@limiter.limit(get_rate_limit("read_operations"))
async def list_api_keys(
    request: Request,  # MEDIUM-005: Required for rate limiter
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    List all API keys (masked, requires authentication).

    MEDIUM-004 fix: Optimized query that checks for encrypted field existence
    using SQL IS NOT NULL instead of decrypting all values. This reduces
    CPU usage and prevents exposing decrypted keys in memory unnecessarily.
    """
    # MEDIUM-004: Query only non-encrypted columns + existence checks for encrypted ones
    # This avoids decrypting all API keys just to list them
    query = select(
        APIKey.id,
        APIKey.service_name,
        APIKey.is_active,
        # Check if encrypted fields have data without decrypting
        case((APIKey.api_key.isnot(None), True), else_=False).label("has_api_key"),
        case((APIKey.access_token.isnot(None), True), else_=False).label("has_access_token"),
        case(
            (
                (APIKey.client_id.isnot(None)) & (APIKey.client_secret.isnot(None)),
                True,
            ),
            else_=False,
        ).label("has_client_credentials"),
        APIKey.last_validated,
        APIKey.created_at,
        APIKey.updated_at,
    )

    result = await db.execute(query)
    rows = result.all()

    # Convert to response schema directly from query results
    return [
        APIKeyMasked(
            id=row.id,
            service_name=row.service_name,
            is_active=row.is_active,
            has_api_key=row.has_api_key,
            has_access_token=row.has_access_token,
            has_client_credentials=row.has_client_credentials,
            last_validated=row.last_validated,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.post("/api-keys", response_model=APIKeyMasked, status_code=201)
@limiter.limit(get_rate_limit("settings_write"))
async def create_or_update_api_key(
    request: Request,  # MEDIUM-005: Required for rate limiter
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Create or update an API key (requires authentication, rate limited)."""
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
@limiter.limit(get_rate_limit("connection_test"))
async def test_connection(
    request: Request,  # MEDIUM-005: Required for rate limiter
    test_data: ConnectionTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Test API connection for a service (requires authentication, rate limited)."""
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
@limiter.limit(get_rate_limit("settings_write"))
async def delete_api_key(
    request: Request,  # MEDIUM-005: Required for rate limiter
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
