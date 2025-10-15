"""
ABOUTME: Rate limiting middleware using SlowAPI to prevent abuse and control costs.
ABOUTME: Uses Redis for distributed rate limit storage and tracking.
"""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses IP address for now. In future with auth, will use user ID.

    Args:
        request: FastAPI request object

    Returns:
        Identifier string for rate limiting
    """
    # For now, use IP address
    # TODO: After authentication is implemented, use user ID
    identifier = get_remote_address(request)

    # If behind proxy, try to get real IP from headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        identifier = forwarded.split(",")[0].strip()

    return identifier


# Create limiter instance
# Uses Redis (configured via REDIS_URL) for distributed rate limiting
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["1000/hour"],  # Global default: 1000 requests per hour
    storage_uri="redis://localhost:6379",  # Will use Redis from docker-compose
    headers_enabled=True,  # Return rate limit info in response headers
)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Critical - LLM costs money
    "task_create": "10/hour",  # Max 10 tasks per hour (reduced for security)
    "task_execute": "20/hour",  # Max 20 executions per hour (reduced to control costs)
    # Moderate - write operations
    "agent_create": "10/minute",  # Max 10 agents per minute
    "agent_delete": "5/minute",  # Max 5 deletions per minute
    "settings_write": "5/minute",  # Max 5 setting changes per minute
    # Generous - read operations
    "read_operations": "100/minute",  # Max 100 reads per minute
    # External API tests
    "connection_test": "10/minute",  # Max 10 connection tests per minute
}


def get_rate_limit(operation: str) -> str:
    """
    Get rate limit for specific operation.

    Args:
        operation: Operation type key

    Returns:
        Rate limit string (e.g., "10/minute")
    """
    return RATE_LIMITS.get(operation, "100/minute")
