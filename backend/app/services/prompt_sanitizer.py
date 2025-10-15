"""
ABOUTME: Prompt sanitization service to prevent LLM prompt injection attacks.
ABOUTME: Validates and sanitizes user inputs before sending to LLM services.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PromptSanitizer:
    """Sanitize user inputs to prevent prompt injection."""

    # Blacklisted patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system[:\s]*new\s+instructions",
        r"</s>",  # End of sequence tokens
        r"<\|.*?\|>",  # Special tokens like <|system|>
        r"SYSTEM:",
        r"---END",
        r"[Aa]dmin\s+mode",
        r"[Dd]ebug\s+mode",
        r"output\s+(all\s+)?(api\s+)?keys",
        r"environment\s+variables",
        r"bypass\s+security",
        r"jailbreak",
        r"prompt\s+injection",
    ]

    @staticmethod
    def sanitize(text: Optional[str], max_length: int = 10000) -> str:
        """
        Sanitize user input to prevent prompt injection.

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            ValueError: If injection pattern detected or input invalid
        """
        if not text:
            return ""

        # Enforce length limit
        if len(text) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")

        # Check for injection patterns
        for pattern in PromptSanitizer.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential prompt injection detected: {pattern}")
                raise ValueError(
                    "Potential prompt injection detected. " "Please rephrase your input."
                )

        # Remove control characters except newlines and tabs
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Normalize excessive whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized

    @staticmethod
    def validate_system_prompt(prompt: str) -> str:
        """
        Validate and sanitize system prompt with stricter rules.

        Args:
            prompt: System prompt to validate

        Returns:
            Validated prompt

        Raises:
            ValueError: If prompt is invalid or contains injection patterns
        """
        # System prompts have stricter limits
        if len(prompt) > 5000:
            raise ValueError("System prompt too long (max 5000 characters)")

        # Apply standard sanitization
        return PromptSanitizer.sanitize(prompt, max_length=5000)

    @staticmethod
    def validate_agent_name(name: str) -> str:
        """
        Validate agent name with strict rules.

        Args:
            name: Agent name to validate

        Returns:
            Validated name

        Raises:
            ValueError: If name is invalid
        """
        if not name or len(name) > 100:
            raise ValueError("Agent name must be 1-100 characters")

        # Only allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r"^[\w\s\-]+$", name):
            raise ValueError(
                "Name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

        return name.strip()

    @staticmethod
    def validate_description(description: str) -> str:
        """
        Validate and sanitize description text.

        Args:
            description: Description to validate

        Returns:
            Validated description

        Raises:
            ValueError: If description is invalid
        """
        if not description or len(description) > 1000:
            raise ValueError("Description must be 1-1000 characters")

        # Remove potential HTML/script tags
        cleaned = re.sub(r"<[^>]+>", "", description)

        # Apply standard sanitization
        return PromptSanitizer.sanitize(cleaned, max_length=1000)
