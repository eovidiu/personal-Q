"""
ABOUTME: Rate limiting middleware using SlowAPI to prevent abuse and control costs.
ABOUTME: Uses Redis for distributed rate limit storage and tracking.
"""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from config.settings import settings

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
    # SECURITY FIX: Prevent rate limiting bypass via header spoofing (CVE-004)
    # Only trust X-Forwarded-For header from known reverse proxies

    # List of trusted proxy IPs (configure based on your deployment)
    # In production, this should be loaded from environment config
    TRUSTED_PROXIES = {
        "127.0.0.1",  # localhost
        "172.16.0.0/12",  # Docker default network range
        "10.0.0.0/8",  # Private network range
    }

    # Get the immediate client IP
    client_ip = get_remote_address(request)

    # Check if the client is a trusted proxy
    from ipaddress import ip_address, ip_network

    try:
        client_addr = ip_address(client_ip) if client_ip else None
        is_trusted_proxy = False

        if client_addr:
            for trusted in TRUSTED_PROXIES:
                if "/" in trusted:
                    # It's a network range
                    if client_addr in ip_network(trusted):
                        is_trusted_proxy = True
                        break
                else:
                    # It's a single IP
                    if str(client_addr) == trusted:
                        is_trusted_proxy = True
                        break

        # Only use X-Forwarded-For if request is from trusted proxy
        if is_trusted_proxy:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                # Get the first IP in the chain (original client)
                identifier = forwarded.split(",")[0].strip()
                logger.debug(
                    f"Using X-Forwarded-For IP: {identifier} (via trusted proxy {client_ip})"
                )
                return identifier
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid IP address format: {e}")

    # Default to direct client IP
    return client_ip or "unknown"


# Create limiter instance
# Uses Redis (configured via REDIS_URL) for distributed rate limiting
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["1000/hour"],  # Global default: 1000 requests per hour
    storage_uri=settings.redis_url,  # Redis URL from environment settings
    headers_enabled=False,  # Disabled to avoid SlowAPI response parameter requirement
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
