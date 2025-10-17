"""
ABOUTME: Standard error response schemas for API consistency.
ABOUTME: Provides unified error format across all endpoints for better client handling.
"""

from typing import List, Optional

from app.utils.datetime_utils import utcnow
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information for specific fields or issues."""

    code: str = Field(..., description="Error code (e.g., 'INVALID_EMAIL')")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if validation error")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_EMAIL",
                "message": "Email format is invalid",
                "field": "email",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format for all API errors."""

    error: str = Field(..., description="Error type or summary")
    detail: Optional[str] = Field(None, description="Detailed error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")
    errors: Optional[List[ErrorDetail]] = Field(None, description="List of specific errors")
    timestamp: str = Field(
        default_factory=lambda: utcnow().isoformat(), description="ISO timestamp"
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation Error",
                "detail": "Invalid input data provided",
                "code": "VALIDATION_ERROR",
                "errors": [
                    {"code": "REQUIRED_FIELD", "message": "This field is required", "field": "name"}
                ],
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "a1b2c3d4",
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific details."""

    error: str = "Validation Error"
    code: str = "VALIDATION_ERROR"
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")


class NotFoundErrorResponse(ErrorResponse):
    """Resource not found error response."""

    error: str = "Not Found"
    code: str = "NOT_FOUND"
    detail: str = Field(..., description="Description of what was not found")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Not Found",
                "detail": "Agent with ID 'abc123' not found",
                "code": "NOT_FOUND",
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "a1b2c3d4",
            }
        }


class UnauthorizedErrorResponse(ErrorResponse):
    """Unauthorized access error response."""

    error: str = "Unauthorized"
    code: str = "UNAUTHORIZED"
    detail: str = Field(..., description="Reason for authorization failure")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Unauthorized",
                "detail": "Invalid or missing authentication token",
                "code": "UNAUTHORIZED",
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "a1b2c3d4",
            }
        }


class ForbiddenErrorResponse(ErrorResponse):
    """Forbidden access error response."""

    error: str = "Forbidden"
    code: str = "FORBIDDEN"
    detail: str = Field(..., description="Reason for access denial")


class ConflictErrorResponse(ErrorResponse):
    """Conflict error response (e.g., duplicate resource)."""

    error: str = "Conflict"
    code: str = "CONFLICT"
    detail: str = Field(..., description="Description of the conflict")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Conflict",
                "detail": "Agent with name 'MyAgent' already exists",
                "code": "CONFLICT",
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "a1b2c3d4",
            }
        }


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit exceeded error response."""

    error: str = "Rate Limit Exceeded"
    code: str = "RATE_LIMIT_EXCEEDED"
    detail: str = "Too many requests, please try again later"


class InternalServerErrorResponse(ErrorResponse):
    """Internal server error response."""

    error: str = "Internal Server Error"
    code: str = "INTERNAL_SERVER_ERROR"
    detail: str = "An unexpected error occurred"

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_SERVER_ERROR",
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "a1b2c3d4",
            }
        }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Service unavailable error response."""

    error: str = "Service Unavailable"
    code: str = "SERVICE_UNAVAILABLE"
    detail: str = Field(..., description="Which service is unavailable")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Service Unavailable",
                "detail": "LLM service is temporarily unavailable",
                "code": "SERVICE_UNAVAILABLE",
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "a1b2c3d4",
            }
        }
