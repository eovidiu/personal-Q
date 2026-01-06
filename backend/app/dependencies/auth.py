"""
Authentication dependencies for protecting routes.
Provides JWT token verification and user extraction.
Supports both HttpOnly cookie auth (OAuth flow) and Bearer token auth (API clients).
"""

import logging
from typing import Dict, Optional

import jwt
from config.settings import settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Dict[str, str]:
    """
    Verify JWT token and return current user information.

    HIGH-003 fix: Supports both HttpOnly cookie (OAuth flow) and Bearer token (API clients).
    Cookie takes precedence for browser-based auth flow.

    Args:
        request: FastAPI request object (for cookie access)
        credentials: HTTP Authorization credentials with Bearer token (optional)

    Returns:
        User information dict with email

    Raises:
        HTTPException: If token is invalid, expired, or user not authorized
    """
    token = None

    # HIGH-003 fix: Try HttpOnly cookie first (from OAuth flow)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        token = cookie_token

    # Fall back to Authorization header (for API clients/tests)
    if not token and credentials is not None:
        token = credentials.credentials

    # SECURITY FIX: Authentication is always required, no exceptions
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

        email = payload.get("email")

        # Verify email is in the allowed list
        if not settings.is_email_allowed(email or ""):
            logger.warning(f"Token contains unauthorized email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource",
            )

        return {"email": email, "sub": payload.get("sub", email)}

    except jwt.ExpiredSignatureError:
        logger.warning("Expired token used in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication failed"
        )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[Dict[str, str]]:
    """
    Get current user if token is provided, otherwise return None.
    Useful for optional authentication on endpoints.

    HIGH-003 fix: Also checks HttpOnly cookies for OAuth flow.

    Args:
        request: FastAPI request object (for cookie access)
        credentials: HTTP Authorization credentials (optional)

    Returns:
        User information dict or None if no token provided
    """
    # Check if there's any auth (cookie or header)
    has_cookie = request.cookies.get("access_token") is not None
    has_header = credentials is not None

    if not has_cookie and not has_header:
        return None

    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None
