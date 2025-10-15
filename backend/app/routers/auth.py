"""
ABOUTME: Google OAuth authentication router for single-user system.
ABOUTME: Implements login, callback, logout, and session verification.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from typing import Optional
import logging
from datetime import timedelta
import jwt

from config.settings import settings
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)

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
async def login(request: Request):
    """
    Initiate Google OAuth login flow.

    Redirects user to Google login page.
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    # Redirect to Google OAuth
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request):
    """
    Handle OAuth callback from Google.

    Verifies user email and creates session token.
    """
    try:
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

        # Redirect to frontend with token
        frontend_url = (
            settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:5173"
        )
        redirect_url = f"{frontend_url}/?token={access_token}"

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again.",
        )


@router.post("/logout")
async def logout():
    """
    Logout (client-side token deletion).

    Returns success message. Client should delete token.
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user info.

    Requires valid JWT token in Authorization header.
    """
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return {"email": payload.get("email"), "authenticated": True}


@router.get("/verify")
async def verify_token_endpoint(request: Request):
    """
    Verify if token is valid.

    Returns:
        Verification status
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"valid": False, "message": "No token provided"}

    token = auth_header.split(" ")[1]
    payload = verify_access_token(token)

    if not payload:
        return {"valid": False, "message": "Invalid or expired token"}

    return {"valid": True, "email": payload.get("email")}
