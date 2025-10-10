"""
Authentication dependencies for protecting routes.
Provides JWT token verification and user extraction.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import logging
import jwt

from config.settings import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    Verify JWT token and return current user information.
    
    Args:
        credentials: HTTP Authorization credentials with Bearer token
        
    Returns:
        User information dict with email
        
    Raises:
        HTTPException: If token is invalid, expired, or user not authorized
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=["HS256"]
        )
        
        email = payload.get("email")
        
        # Verify email matches allowed user
        if email != settings.allowed_email:
            logger.warning(f"Token contains unauthorized email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource"
            )
        
        return {
            "email": email,
            "sub": payload.get("sub", email)
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token used in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, str]]:
    """
    Get current user if token is provided, otherwise return None.
    Useful for optional authentication on endpoints.
    
    Args:
        credentials: HTTP Authorization credentials (optional)
        
    Returns:
        User information dict or None if no token provided
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
