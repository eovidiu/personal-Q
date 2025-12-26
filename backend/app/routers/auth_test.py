"""
ABOUTME: Test-only authentication endpoint for E2E testing with Playwright.
ABOUTME: Provides JWT tokens without Google OAuth for automated test environments.
ABOUTME: SECURITY: Quad-layer validation ensures this is NEVER available in production.

SECURITY ARCHITECTURE (HIGH-002 fix):
- Layer 1 (Import-time): Multi-factor production detection blocks import
- Layer 2 (Registration): Router only included in main.py for non-production
- Layer 3 (Runtime): Endpoints return 404 if somehow accessed in production
- Layer 4 (Startup): main.py validates test routes not registered in production

This file should ONLY be imported in test/development environments.
"""

import logging
import os
import socket

from app.routers.auth import create_access_token
from config.settings import settings
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

logger = logging.getLogger(__name__)


def _is_production_environment() -> bool:
    """
    Multi-factor production detection (HIGH-002 fix).

    Returns True if ANY production indicator is present.
    This provides defense-in-depth against misconfigured ENV variable.
    """
    # Check 1: Explicit ENV variable (primary)
    if settings.env == "production":
        return True

    # Check 2: Railway production environment
    if os.getenv("RAILWAY_ENVIRONMENT") == "production":
        logger.warning("Production detected via RAILWAY_ENVIRONMENT")
        return True

    # Check 3: Render production (not a PR preview)
    if os.getenv("RENDER") and not os.getenv("IS_PULL_REQUEST"):
        # RENDER_EXTERNAL_URL indicates production Render deployment
        if os.getenv("RENDER_EXTERNAL_URL"):
            logger.warning("Production detected via RENDER environment")
            return True

    # Check 4: Hostname-based detection
    try:
        hostname = socket.gethostname().lower()
        prod_indicators = ["prod", "production", "live"]
        if any(ind in hostname for ind in prod_indicators):
            logger.warning(f"Production detected via hostname: {hostname}")
            return True
    except Exception:
        pass  # Hostname check failed, continue with other checks

    # Check 5: Fly.io production
    if os.getenv("FLY_APP_NAME") and os.getenv("FLY_REGION"):
        # If FLY_ALLOC_ID exists, it's a running Fly machine
        if os.getenv("FLY_ALLOC_ID"):
            logger.warning("Production detected via Fly.io environment")
            return True

    return False


# SECURITY LAYER 1: Import-time validation with multi-factor detection
# Prevent this module from being imported in production environments
if _is_production_environment():
    # Clear this module from cache to prevent reuse if ENV changes
    import sys

    module_name = __name__
    if module_name in sys.modules:
        del sys.modules[module_name]

    raise RuntimeError(
        "SECURITY ERROR: auth_test.py cannot be imported in production environment. "
        "This module provides test-only authentication bypass and must never be "
        "available in production. Check your imports and environment configuration."
    )

logger.warning(
    f"⚠️  TEST AUTH MODULE LOADED - Environment: {settings.env} "
    f"(This should NEVER appear in production logs)"
)


class TestLoginRequest(BaseModel):
    """Request model for test login endpoint."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Validate email matches allowed user.

        SECURITY: Does NOT reveal ALLOWED_EMAIL to prevent enumeration attacks.
        """
        if not settings.allowed_email:
            raise ValueError("Test authentication not available: system not configured.")

        if v != settings.allowed_email:
            # SECURITY: Generic error message prevents email enumeration
            raise ValueError("Email not authorized for test authentication.")

        return v


class TestLoginResponse(BaseModel):
    """Response model for test login endpoint."""

    access_token: str
    token_type: str = "bearer"
    email: str


router = APIRouter()


def _validate_test_environment() -> None:
    """
    SECURITY LAYER 3: Runtime validation with multi-factor detection (HIGH-002 fix).

    Validates that current environment allows test auth.
    Uses same multi-factor detection as import-time check for defense-in-depth.
    Raises HTTPException if accessed in production.
    """
    if _is_production_environment():
        logger.error(
            "🚨 SECURITY ALERT: Test auth endpoint accessed in production environment! "
            "This endpoint should be completely disabled in production. "
            f"Detection method: ENV={settings.env}, RAILWAY={os.getenv('RAILWAY_ENVIRONMENT')}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",  # Don't reveal endpoint exists
        )

    if not settings.allowed_email:
        logger.error("Test auth endpoint accessed but ALLOWED_EMAIL not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Test authentication not available: system not configured",
        )


@router.post("/test-login", response_model=TestLoginResponse)
# Note: Rate limiting removed from test endpoint - it's already triple-layer secured
async def test_login(login_request: TestLoginRequest) -> TestLoginResponse:
    """
    TEST-ONLY: Generate JWT token for automated testing.

    This endpoint bypasses Google OAuth and directly generates a JWT token
    for the configured ALLOWED_EMAIL. It is designed for Playwright E2E tests.

    Security guarantees:
    - Only available in test/development environments (triple-layer validation)
    - Only generates tokens for ALLOWED_EMAIL (single-user validation)
    - Uses same JWT generation logic as production OAuth flow
    - All access attempts are logged for security audit

    Args:
        login_request: Login request with email

    Returns:
        TestLoginResponse with JWT access token

    Raises:
        HTTPException: 404 if accessed in production
        HTTPException: 403 if email not authorized
        HTTPException: 503 if system not configured
    """
    # SECURITY LAYER 3: Runtime environment validation
    _validate_test_environment()

    # Log test authentication attempt for security audit
    logger.warning(
        f"⚠️  TEST AUTH: Generating token for {login_request.email} "
        f"(Environment: {settings.env}, Debug: {settings.debug})"
    )

    # Generate real JWT token using production logic
    # This ensures test tokens match production token format and validation
    access_token = create_access_token(login_request.email)

    logger.info(f"✓ Test token generated for {login_request.email}")

    return TestLoginResponse(
        access_token=access_token,
        token_type="bearer",
        email=login_request.email,
    )


@router.get("/test-validate")
async def test_validate() -> dict:
    """
    TEST-ONLY: Validate test auth endpoint is accessible.

    Returns minimal validation info without exposing sensitive configuration.
    LOW-001 fix: Removed debug_mode and allowed_email from response to prevent
    configuration leakage that could aid attackers.

    Returns:
        dict: Environment validation info (minimal, non-sensitive)
    """
    _validate_test_environment()

    # LOW-001: Only return minimal, non-sensitive information
    # Do not expose: debug_mode, allowed_email, or other configuration
    return {
        "test_auth_available": True,
        "environment": settings.env,  # Already known from deployment context
        "message": "Test authentication endpoint is accessible",
    }
