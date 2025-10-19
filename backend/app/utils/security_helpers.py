"""
Security helper functions for Personal-Q application.
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def sanitize_error_for_client(error: Exception) -> str:
    """
    Sanitize error messages before sending to clients.
    Removes sensitive information like file paths, credentials, etc.

    Args:
        error: The exception to sanitize

    Returns:
        A user-friendly error message
    """
    error_str = str(error)

    # Map specific error types to user-friendly messages
    error_type_messages = {
        "ConnectionError": "Connection failed. Please try again.",
        "TimeoutError": "Operation timed out. Please try again.",
        "ValidationError": "Invalid input provided.",
        "AuthenticationError": "Authentication failed.",
        "PermissionError": "Permission denied.",
        "DatabaseError": "Database operation failed.",
    }

    # Check for known error types
    for error_type, message in error_type_messages.items():
        if error_type in str(type(error).__name__):
            return message

    # Remove sensitive patterns
    sensitive_patterns = [
        r'/[\w/]+\.py',  # File paths
        r'line \d+',  # Line numbers
        r'api[_-]?key["\']?\s*[:=]\s*["\']\w+["\']',  # API keys
        r'password["\']?\s*[:=]\s*["\']\w+["\']',  # Passwords
        r'token["\']?\s*[:=]\s*["\']\w+["\']',  # Tokens
        r'secret["\']?\s*[:=]\s*["\']\w+["\']',  # Secrets
        r'localhost:\d+',  # Internal endpoints
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
    ]

    sanitized = error_str
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)

    # If the error is still too detailed, return generic message
    if len(sanitized) > 200 or '[REDACTED]' in sanitized:
        return "An error occurred. Please try again or contact support."

    return sanitized


def sanitize_prompt(prompt: str, system_prompt: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Sanitize user prompts and system prompts to prevent injection attacks.

    Args:
        prompt: User-provided prompt
        system_prompt: System prompt for the agent

    Returns:
        Tuple of (sanitized_prompt, sanitized_system_prompt)

    Raises:
        ValueError: If dangerous injection patterns are detected
    """
    def check_and_sanitize(text: str, context: str = "prompt") -> str:
        if not text:
            return text

        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # Dangerous patterns that should be blocked
        dangerous_patterns = [
            (r'(?i)(system|assistant|user)\s*:', "Role hijacking attempt"),
            (r'<\|im_start\|>.*?<\|im_end\|>', "Token smuggling attempt"),
            (r'###\s*(system|instruction|assistant)', "Instruction override attempt"),
            (r'(?i)ignore\s+(all\s+)?previous\s+instructions', "Instruction bypass attempt"),
            (r'(?i)forget\s+everything', "Context reset attempt"),
            (r'(?i)you\s+are\s+now\s+(a|an|the)', "Identity override attempt"),
            (r'(?i)disregard\s+(all\s+)?safety', "Safety bypass attempt"),
            (r'(?i)output\s+all\s+(api\s+)?keys', "Credential extraction attempt"),
            (r'(?i)reveal\s+your\s+instructions', "Instruction extraction attempt"),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, text):
                logger.warning(f"Blocked prompt injection in {context}: {description}")
                raise ValueError(f"Invalid {context}: contains forbidden patterns")

        # Warning patterns (log but allow)
        warning_patterns = [
            r'(?i)pretend\s+to\s+be',
            r'(?i)act\s+as\s+if',
            r'(?i)simulate',
            r'(?i)roleplay',
        ]

        for pattern in warning_patterns:
            if re.search(pattern, text):
                logger.info(f"Potential roleplay pattern in {context}, allowing but monitoring")

        return text

    # Sanitize both prompts
    sanitized_prompt = check_and_sanitize(prompt, "user prompt")
    sanitized_system = check_and_sanitize(system_prompt, "system prompt") if system_prompt else None

    # Add safety boundaries to user prompt
    bounded_prompt = f"<user_input>\n{sanitized_prompt}\n</user_input>"

    return bounded_prompt, sanitized_system


def verify_task_ownership(task: Any, current_user: Dict, allow_admin: bool = False) -> bool:
    """
    Verify that a user owns a task or has permission to access it.

    Args:
        task: Task object with agent relationship
        current_user: Current user dict from JWT
        allow_admin: Whether to allow admin users full access

    Returns:
        True if user has permission, False otherwise
    """
    # In single-user mode, check against allowed email
    user_email = current_user.get("email")

    if not user_email:
        logger.warning("No email in current_user dict")
        return False

    # For future multi-user support, would check task.agent.user_id
    # Currently all tasks belong to the single allowed user
    # This is a placeholder for proper authorization

    # Check if user is admin (future feature)
    if allow_admin and current_user.get("is_admin"):
        return True

    # In production, would check: task.agent.user_id == current_user["id"]
    # For now, just verify the user is authenticated (single-user mode)
    return user_email is not None


def classify_error_type(error: Exception) -> str:
    """
    Classify an error into a category for client-side handling.

    Args:
        error: The exception to classify

    Returns:
        Error category string
    """
    error_classifications = {
        ConnectionError: "network_error",
        TimeoutError: "timeout_error",
        ValueError: "validation_error",
        PermissionError: "permission_error",
        FileNotFoundError: "not_found_error",
        KeyError: "configuration_error",
    }

    for error_class, classification in error_classifications.items():
        if isinstance(error, error_class):
            return classification

    # Check error message for patterns
    error_str = str(error).lower()
    if "timeout" in error_str:
        return "timeout_error"
    elif "connection" in error_str or "network" in error_str:
        return "network_error"
    elif "permission" in error_str or "forbidden" in error_str:
        return "permission_error"
    elif "not found" in error_str or "404" in error_str:
        return "not_found_error"
    elif "validation" in error_str or "invalid" in error_str:
        return "validation_error"

    return "unknown_error"


def validate_websocket_message_size(message: Dict[str, Any], max_size_kb: int = 1024) -> bool:
    """
    Validate that a WebSocket message doesn't exceed size limits.

    Args:
        message: Message dictionary to validate
        max_size_kb: Maximum size in kilobytes

    Returns:
        True if message is within limits, False otherwise
    """
    import json

    try:
        message_str = json.dumps(message)
        size_kb = len(message_str.encode('utf-8')) / 1024

        if size_kb > max_size_kb:
            logger.warning(f"WebSocket message too large: {size_kb:.2f}KB > {max_size_kb}KB")
            return False

        return True
    except Exception as e:
        logger.error(f"Error validating message size: {e}")
        return False