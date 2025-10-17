"""
ABOUTME: Custom exception classes for Personal-Q application.
ABOUTME: Provides specific exception types for better error handling and debugging.
"""

__all__ = [
    "PersonalQException",
    "AgentNotFoundException",
    "TaskNotFoundException",
    "TaskExecutionError",
    "LLMServiceError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "IntegrationError",
    "SlackIntegrationError",
    "MicrosoftGraphError",
    "ObsidianIntegrationError",
    "ChromaDBError",
    "CacheError",
    "ConfigurationError",
    "ValidationError",
    "DuplicateResourceError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError",
]


class PersonalQException(Exception):
    """Base exception for all Personal-Q errors."""

    pass


class AgentNotFoundException(PersonalQException):
    """Raised when an agent is not found in the database."""

    pass


class TaskNotFoundException(PersonalQException):
    """Raised when a task is not found in the database."""

    pass


class TaskExecutionError(PersonalQException):
    """Raised when task execution fails."""

    pass


class LLMServiceError(PersonalQException):
    """Raised when LLM service encounters an error."""

    pass


class LLMRateLimitError(LLMServiceError):
    """Raised when LLM rate limit is exceeded."""

    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when LLM request times out."""

    pass


class IntegrationError(PersonalQException):
    """Base exception for external integration failures."""

    pass


class SlackIntegrationError(IntegrationError):
    """Raised when Slack integration fails."""

    pass


class MicrosoftGraphError(IntegrationError):
    """Raised when Microsoft Graph API fails."""

    pass


class ObsidianIntegrationError(IntegrationError):
    """Raised when Obsidian vault operation fails."""

    pass


class ChromaDBError(PersonalQException):
    """Raised when ChromaDB operation fails."""

    pass


class CacheError(PersonalQException):
    """Raised when cache operation fails."""

    pass


class ConfigurationError(PersonalQException):
    """Raised when configuration is invalid or missing."""

    pass


class ValidationError(PersonalQException):
    """Raised when input validation fails."""

    pass


class DuplicateResourceError(PersonalQException):
    """Raised when attempting to create a duplicate resource."""

    pass


class AuthenticationError(PersonalQException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(PersonalQException):
    """Raised when user lacks permission for an action."""

    pass


class DatabaseError(PersonalQException):
    """Raised when database operation fails."""

    pass
