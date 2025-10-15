"""
ABOUTME: Request logging middleware for observability and monitoring.
ABOUTME: Tracks request duration, status codes, and adds request IDs for tracing.
"""

import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Context variable for request ID (thread-safe)
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests with timing and status information."""

    async def dispatch(self, request: Request, call_next):
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]  # Short ID for readability
        request_id_var.set(request_id)

        # Record start time
        start_time = time.time()

        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Log request completion
            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING

            logger.log(
                log_level,
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration_ms}ms "
                f"request_id={request_id}",
            )

            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log exception
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration_ms}ms request_id={request_id}",
                exc_info=True,
            )
            raise


class PerformanceLogger:
    """Helper for logging performance metrics."""

    @staticmethod
    def log_operation(operation: str, duration_ms: float, success: bool = True, **kwargs):
        """
        Log an operation with timing information.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            **kwargs: Additional context
        """
        context = " ".join(f"{k}={v}" for k, v in kwargs.items())
        status = "success" if success else "failed"

        logger.info(f"Operation {operation} {status} in {duration_ms}ms {context}")


class SecurityLogger:
    """Helper for logging security events."""

    @staticmethod
    def log_api_key_access(action: str, service: str, user_id: str = None):
        """
        Log API key access for security auditing.

        Args:
            action: Action performed (read/write/delete)
            service: Service name (anthropic, slack, etc.)
            user_id: User ID if available
        """
        logger.warning(
            f"Security event: API key access - action={action} "
            f"service={service} user_id={user_id or 'unknown'}"
        )

    @staticmethod
    def log_auth_attempt(success: bool, user_id: str = None, reason: str = None):
        """
        Log authentication attempt.

        Args:
            success: Whether auth succeeded
            user_id: User ID if available
            reason: Failure reason if failed
        """
        status = "success" if success else "failed"
        reason_str = f"reason={reason}" if reason else ""

        logger.warning(
            f"Security event: Authentication {status} - "
            f"user_id={user_id or 'unknown'} {reason_str}"
        )

    @staticmethod
    def log_suspicious_activity(activity: str, details: str, request_id: str = None):
        """
        Log suspicious activity for security monitoring.

        Args:
            activity: Activity description
            details: Additional details
            request_id: Request ID if available
        """
        request_id = request_id or request_id_var.get()
        logger.error(
            f"Security event: Suspicious activity - {activity} "
            f"details={details} request_id={request_id}"
        )


# Global instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
