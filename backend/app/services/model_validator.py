"""
ABOUTME: Model string validation and normalization for LLM providers.
ABOUTME: Handles legacy model names and ensures valid provider/model format.
"""

import logging
import re
from typing import Optional, Tuple

from app.schemas.llm import ValidationResult
from app.services.provider_registry import ProviderRegistry, provider_registry

logger = logging.getLogger(__name__)

# Valid model string pattern: provider/model-name
# Allows: letters, numbers, hyphens, underscores, periods
VALID_MODEL_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$")


class ModelValidator:
    """
    Validates and normalizes model strings.

    Handles:
    - Provider prefix parsing ("anthropic/claude-3-opus" -> "anthropic", "claude-3-opus")
    - Legacy model names ("GPT-4" -> "openai/gpt-4")
    - Model existence validation
    - Provider availability checking
    """

    # Legacy model name mappings (for backwards compatibility)
    # Maps old/informal names to proper provider/model format
    LEGACY_MAPPINGS = {
        # OpenAI legacy names
        "gpt-4": "openai/gpt-4",
        "gpt-4-turbo": "openai/gpt-4-turbo",
        "gpt-4o": "openai/gpt-4o",
        "gpt-4o-mini": "openai/gpt-4o-mini",
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        "gpt-3.5": "openai/gpt-3.5-turbo",
        # Case-insensitive common names
        "GPT-4": "openai/gpt-4",
        "GPT-4-Turbo": "openai/gpt-4-turbo",
        "GPT-4o": "openai/gpt-4o",
        "GPT-3.5": "openai/gpt-3.5-turbo",
        "GPT-3.5-Turbo": "openai/gpt-3.5-turbo",
        # Anthropic legacy names
        "claude-3-opus": "anthropic/claude-3-opus-20240229",
        "claude-3-sonnet": "anthropic/claude-3-sonnet-20240229",
        "claude-3-haiku": "anthropic/claude-3-haiku-20240307",
        "claude-3.5-sonnet": "anthropic/claude-3-5-sonnet-20241022",
        "claude-3.5-haiku": "anthropic/claude-3-5-haiku-20241022",
        "claude-3.7-sonnet": "anthropic/claude-3-7-sonnet-20250219",
        "claude-sonnet-4": "anthropic/claude-sonnet-4-20250514",
        "claude-opus-4": "anthropic/claude-opus-4-20250514",
        # Common informal names
        "Claude-3": "anthropic/claude-3-5-sonnet-20241022",
        "Claude-3.5": "anthropic/claude-3-5-sonnet-20241022",
        "Claude": "anthropic/claude-3-5-sonnet-20241022",
        # Mistral legacy names
        "mistral-large": "mistral/mistral-large-latest",
        "mistral-medium": "mistral/mistral-medium-latest",
        "mistral-small": "mistral/mistral-small-latest",
        "codestral": "mistral/codestral-latest",
        "mixtral": "mistral/open-mixtral-8x7b",
        # Gemini legacy names (for future use)
        "gemini-pro": "gemini/gemini-1.5-pro",
        "gemini-flash": "gemini/gemini-1.5-flash",
        "Gemini-Pro": "gemini/gemini-1.5-pro",
    }

    def __init__(self, registry: Optional[ProviderRegistry] = None):
        self.registry = registry or provider_registry

    def parse_model_string(self, model: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse model string into (provider, model).

        Examples:
            "anthropic/claude-3-opus" -> ("anthropic", "claude-3-opus")
            "openai/gpt-4" -> ("openai", "gpt-4")
            "GPT-4" -> (None, "GPT-4")  # No provider prefix

        Returns:
            (provider, model) tuple. Provider is None if no prefix found.
        """
        if "/" in model:
            parts = model.split("/", 1)
            return (parts[0].lower(), parts[1])
        return (None, model)

    def normalize_legacy_model(self, model: str) -> Optional[str]:
        """
        Normalize legacy model names to provider-prefixed format.

        Examples:
            "GPT-4" -> "openai/gpt-4"
            "claude-3-opus" -> "anthropic/claude-3-opus-20240229"
            "anthropic/claude-3-opus" -> "anthropic/claude-3-opus" (unchanged)

        Returns:
            Normalized model string, or None if not recognized.
        """
        # If already has prefix, return as-is
        if "/" in model:
            return model

        # Check legacy mappings (case-sensitive first, then case-insensitive)
        if model in self.LEGACY_MAPPINGS:
            normalized = self.LEGACY_MAPPINGS[model]
            logger.info(f"Normalized legacy model '{model}' to '{normalized}'")
            return normalized

        # Try case-insensitive lookup
        model_lower = model.lower()
        for key, value in self.LEGACY_MAPPINGS.items():
            if key.lower() == model_lower:
                logger.info(f"Normalized legacy model '{model}' to '{value}' (case-insensitive)")
                return value

        return None

    def validate_model(self, model: str, check_configured: bool = True) -> ValidationResult:
        """
        Validate model string.

        Steps:
        1. Parse provider prefix
        2. If no prefix, check legacy mappings
        3. Validate provider exists
        4. Optionally check if provider is configured
        5. Validate model exists for provider

        Args:
            model: Model string to validate (e.g., "anthropic/claude-3-5-sonnet-20241022")
            check_configured: Whether to verify API key is configured

        Returns:
            ValidationResult with details.
        """
        if not model or not model.strip():
            return ValidationResult(
                is_valid=False,
                error="Model string cannot be empty",
            )

        model = model.strip()

        # Step 1: Try parsing provider prefix
        provider, model_name = self.parse_model_string(model)

        # Step 2: Check legacy mappings if no prefix
        if not provider:
            normalized = self.normalize_legacy_model(model)
            if normalized:
                provider, model_name = self.parse_model_string(normalized)
            else:
                return ValidationResult(
                    is_valid=False,
                    error=f"Unrecognized model format: '{model}'. Use 'provider/model' format "
                    f"(e.g., 'anthropic/claude-3-5-sonnet-20241022', 'openai/gpt-4o').",
                )

        # Step 3: Validate model string format (security check)
        full_model = f"{provider}/{model_name}"
        if not VALID_MODEL_PATTERN.match(full_model):
            return ValidationResult(
                is_valid=False,
                provider=provider,
                model=model_name,
                error=f"Invalid model format: '{full_model}'. "
                f"Model names can only contain letters, numbers, hyphens, underscores, and periods.",
            )

        # Step 4: Validate provider exists
        provider_config = self.registry.get_provider(provider)
        if not provider_config:
            available_providers = ", ".join(
                p.name for p in self.registry.list_providers()
            )
            return ValidationResult(
                is_valid=False,
                provider=provider,
                model=model_name,
                error=f"Unknown provider: '{provider}'. Available providers: {available_providers}",
            )

        # Step 5: Check if provider is configured (optional)
        if check_configured and not provider_config.is_configured:
            return ValidationResult(
                is_valid=False,
                provider=provider,
                model=model_name,
                error=f"Provider '{provider}' not configured. "
                f"Set {provider_config.api_key_env} environment variable.",
            )

        # Step 6: Validate model exists for provider
        valid_models = self.registry.get_model_ids(provider)
        if model_name not in valid_models:
            # Provide helpful suggestions
            suggestions = ", ".join(valid_models[:5])
            return ValidationResult(
                is_valid=False,
                provider=provider,
                model=model_name,
                error=f"Model '{model_name}' not available for provider '{provider}'. "
                f"Available models include: {suggestions}",
            )

        # All checks passed
        normalized_model = f"{provider_config.prefix}{model_name}"
        return ValidationResult(
            is_valid=True,
            provider=provider,
            model=model_name,
            normalized=normalized_model,
        )


# Global singleton instance
model_validator = ModelValidator()


def get_anthropic_api_key() -> str:
    """
    Get Anthropic API key from environment.

    SECURITY: API keys are ONLY read from environment variables.
    They are NEVER stored in the database.

    Returns:
        API key string

    Raises:
        ValueError: If no API key is configured
    """
    api_key = provider_registry.get_api_key("anthropic")
    if not api_key:
        raise ValueError(
            "Anthropic API key not configured. "
            "Set ANTHROPIC_API_KEY or PERSONAL_Q_API_KEY environment variable."
        )
    return api_key
