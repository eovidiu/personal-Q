"""
ABOUTME: Google OAuth authentication router for single-user system.
ABOUTME: Implements login, callback, logout, and session verification.
ABOUTME: Includes CSRF protection via OAuth state parameter stored in Redis.
"""

import json
import logging
import secrets
from datetime import timedelta
from typing import Optional

import jwt
import redis
from app.middleware.rate_limit import limiter
from app.utils.datetime_utils import utcnow
from authlib.integrations.starlette_client import OAuth
from config.settings import settings
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.config import Config

logger = logging.getLogger(__name__)

# Redis client for OAuth state storage (HIGH-001 fix: scalable state management)
_redis_client: Optional[redis.Redis] = None
OAUTH_STATE_TTL = 600  # 10 minutes expiry for OAuth state tokens
OAUTH_STATE_PREFIX = "oauth_state:"


def get_redis_client() -> redis.Redis:
    """Get or create Redis client for OAuth state storage."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client

router = APIRouter()

# Configure OAuth
config = Config(
    environ={
        "GOOGLE_CLIENT_ID": settings.google_client_id or "",
        "GOOGLE_CLIENT_SECRET": settings.google_client_secret or "",
    }
)

oauth = OAuth(config)

# Register Google OAuth provider
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def create_access_token(email: str) -> str:
    """
    Create JWT access token for authenticated user.

    Args:
        email: User email

    Returns:
        JWT token
    """
    now = utcnow()
    payload = {
        "sub": email,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=24),  # 24 hour expiry
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return token


def verify_access_token(token: str) -> Optional[dict]:
    """
    Verify JWT access token.

    Args:
        token: JWT token

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

        # Verify email is the allowed user
        if payload.get("email") != settings.allowed_email:
            logger.warning(
                f"Token email mismatch: {payload.get('email')} != {settings.allowed_email}"
            )
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


@router.get("/login")
@limiter.limit("10/minute")
async def login(request: Request):
    """
    Initiate Google OAuth login flow with CSRF protection.

    Generates a random state token to prevent CSRF attacks.
    State is stored in Redis for horizontal scaling support (HIGH-001 fix).
    Redirects user to Google login page.
    Rate limited to prevent abuse.
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    # Generate CSRF protection state token
    state = secrets.token_urlsafe(32)

    # Store state in Redis with TTL (HIGH-001 fix: Redis instead of in-memory)
    try:
        redis_client = get_redis_client()
        state_data = json.dumps({
            "created_at": utcnow().isoformat(),
            "redirect_uri": str(request.url_for("auth_callback"))
        })
        redis_client.setex(f"{OAUTH_STATE_PREFIX}{state}", OAUTH_STATE_TTL, state_data)
        logger.info(f"Generated OAuth state token: {state[:8]}... (stored in Redis)")
    except redis.RedisError as e:
        logger.error(f"Failed to store OAuth state in Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable.",
        )

    # Redirect to Google OAuth with state parameter
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)


@router.get("/callback")
@limiter.limit("20/minute")
async def auth_callback(request: Request):
    """
    Handle OAuth callback from Google with CSRF validation.

    Verifies state parameter from Redis, user email, and creates session token.
    State is deleted after use to prevent replay attacks (HIGH-001 fix).
    Rate limited to prevent abuse.
    """
    try:
        # Validate CSRF state parameter from Redis (HIGH-001 fix)
        state = request.query_params.get("state")
        if not state:
            logger.warning("Missing OAuth state parameter")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid state parameter. Possible CSRF attack.",
            )

        try:
            redis_client = get_redis_client()
            state_key = f"{OAUTH_STATE_PREFIX}{state}"
            state_data = redis_client.get(state_key)

            if not state_data:
                logger.warning(f"OAuth state not found in Redis: {state[:8]}...")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired state parameter. Please try logging in again.",
                )

            # Delete state immediately to prevent replay attacks
            redis_client.delete(state_key)
            logger.info(f"Validated and consumed OAuth state token: {state[:8]}...")

        except redis.RedisError as e:
            logger.error(f"Redis error during OAuth callback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service temporarily unavailable.",
            )

        # Get OAuth token from Google
        token = await oauth.google.authorize_access_token(request)

        # Get user info
        user_info = token.get("userinfo")
        if not user_info:
            # Fallback to userinfo endpoint
            resp = await oauth.google.get(
                "https://www.googleapis.com/oauth2/v3/userinfo", token=token
            )
            user_info = resp.json()

        email = user_info.get("email")

        # Verify email matches allowed user
        if email != settings.allowed_email:
            logger.warning(f"Unauthorized login attempt from {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Only {settings.allowed_email} is authorized.",
            )

        # Log successful auth
        logger.info(f"User {email} authenticated successfully")

        # Create JWT token
        access_token = create_access_token(email)

        # HIGH-003 fix: Set JWT in HttpOnly cookie instead of URL parameter
        # This prevents token exposure in browser history, logs, and referrer headers
        frontend_url = (
            settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:5173"
        )

        # Redirect to frontend callback (no token in URL)
        response = RedirectResponse(url=f"{frontend_url}/auth/callback")

        # Set secure HttpOnly cookie with JWT
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,  # Not accessible to JavaScript
            secure=settings.env == "production",  # HTTPS only in production
            samesite="lax",  # CSRF protection
            max_age=24 * 60 * 60,  # 24 hours (matches JWT expiry)
            path="/",
        )

        # Issue #111 fix: Set explicit CSRF token for defense-in-depth
        # This provides additional protection beyond SameSite cookies
        csrf_token = secrets.token_urlsafe(32)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,  # Must be readable by JavaScript
            secure=settings.env == "production",
            samesite="strict",  # Stricter than access_token for CSRF protection
            max_age=24 * 60 * 60,
            path="/",
        )

        logger.info(f"OAuth complete for {email}, token set in HttpOnly cookie")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again.",
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout - clears HttpOnly authentication cookie.

    HIGH-003 fix: Properly clears the HttpOnly cookie set during OAuth.
    Issue #111 fix: CSRF protection via explicit token + SameSite cookies.

    Defense-in-depth: We validate CSRF token from header matches cookie.
    This protects even if SameSite restrictions are bypassed (e.g., same-site XSS).
    """
    # Issue #111: Validate CSRF token for defense-in-depth
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")

    # Only enforce CSRF if user has a session (csrf_cookie exists)
    if csrf_cookie:
        if not csrf_header or csrf_cookie != csrf_header:
            logger.warning("Logout CSRF validation failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed"
            )

    # Verify session exists (cookie must be present for logout)
    cookie_token = request.cookies.get("access_token")
    if not cookie_token:
        # No session to logout - but don't leak info, return success
        logger.info("Logout called without active session")
    else:
        # Optional: Verify token is valid (prevents logout of already-invalid sessions)
        payload = verify_access_token(cookie_token)
        if payload:
            logger.info(f"User {payload.get('email')} logged out")
        else:
            logger.info("Logout called with invalid/expired token")

    response = JSONResponse(content={"message": "Logged out successfully"})

    # Clear the HttpOnly cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.env == "production",
        samesite="lax",
    )

    # Issue #111: Also clear the CSRF token cookie
    response.delete_cookie(
        key="csrf_token",
        path="/",
        secure=settings.env == "production",
        samesite="strict",
    )

    return response


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user info.

    HIGH-003 fix: Accepts JWT from HttpOnly cookie OR Authorization header.
    Cookie takes precedence for browser-based auth flow.
    """
    token = None

    # Try HttpOnly cookie first (from OAuth flow)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        token = cookie_token

    # Fall back to Authorization header (for API clients/tests)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return {"email": payload.get("email"), "authenticated": True}


@router.get("/verify")
@limiter.limit("10/minute")
async def verify_token_endpoint(request: Request):
    """
    Verify if token is valid.

    HIGH-003 fix: Accepts JWT from HttpOnly cookie OR Authorization header.
    Rate limited to prevent token enumeration attacks.
    Returns:
        Verification status
    """
    token = None

    # Try HttpOnly cookie first (from OAuth flow)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        token = cookie_token

    # Fall back to Authorization header (for API clients/tests)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return {"valid": False, "message": "No token provided"}

    payload = verify_access_token(token)

    if not payload:
        return {"valid": False, "message": "Invalid or expired token"}

    return {"valid": True, "email": payload.get("email")}
