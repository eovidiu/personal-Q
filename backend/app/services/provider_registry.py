"""
ABOUTME: Registry of LLM providers and their configurations.
ABOUTME: Provides provider enumeration, model validation, and API key checking.
ABOUTME: API keys are NEVER stored - only read from environment variables.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.schemas.llm import ModelInfo, ProviderInfo

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    display_name: str
    prefix: str
    api_key_env: str
    fallback_env: Optional[str] = None
    models: List[ModelInfo] = field(default_factory=list)

    @property
    def is_configured(self) -> bool:
        """
        Check if API key is available in environment.

        SECURITY: Only checks existence, never exposes the key value.
        """
        has_primary = bool(os.getenv(self.api_key_env))
        has_fallback = self.fallback_env and bool(os.getenv(self.fallback_env))
        return has_primary or has_fallback

    def get_api_key(self) -> Optional[str]:
        """
        Get API key from environment.

        SECURITY: API keys are ONLY read from environment variables.
        They are NEVER stored in the database.
        """
        key = os.getenv(self.api_key_env)
        if not key and self.fallback_env:
            key = os.getenv(self.fallback_env)
        return key


class ProviderRegistry:
    """
    Singleton registry of LLM providers and their configurations.

    SECURITY CRITICAL:
    - API keys are NEVER stored in the database
    - API keys are ONLY read from environment variables
    - This class never exposes API key values in responses

    This class:
    - Registers providers at startup
    - Validates model strings
    - Checks API key availability (without exposing keys)
    - Provides provider/model enumeration for API
    """

    _instance: Optional["ProviderRegistry"] = None

    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_providers()
            self._initialized = True

    def _initialize_providers(self) -> None:
        """Initialize all supported providers with their models."""

        # ═══════════════════════════════════════════════════════════════
        # ANTHROPIC (Claude)
        # ═══════════════════════════════════════════════════════════════
        self.register_provider(
            ProviderConfig(
                name="anthropic",
                display_name="Anthropic (Claude)",
                prefix="anthropic/",
                api_key_env="ANTHROPIC_API_KEY",
                fallback_env="PERSONAL_Q_API_KEY",
                models=[
                    # Claude 4 Series (Latest)
                    ModelInfo(
                        id="claude-sonnet-4-20250514",
                        display_name="Claude Sonnet 4",
                        context_window=200000,
                        max_output_tokens=16384,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.003,
                        cost_per_1k_output=0.015,
                        is_recommended=True,
                    ),
                    ModelInfo(
                        id="claude-opus-4-20250514",
                        display_name="Claude Opus 4",
                        context_window=200000,
                        max_output_tokens=32768,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.015,
                        cost_per_1k_output=0.075,
                        is_recommended=False,
                    ),
                    # Claude 3.7 Series
                    ModelInfo(
                        id="claude-3-7-sonnet-20250219",
                        display_name="Claude 3.7 Sonnet",
                        context_window=200000,
                        max_output_tokens=16384,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.003,
                        cost_per_1k_output=0.015,
                        is_recommended=False,
                    ),
                    # Claude 3.5 Series
                    ModelInfo(
                        id="claude-3-5-sonnet-20241022",
                        display_name="Claude 3.5 Sonnet",
                        context_window=200000,
                        max_output_tokens=8192,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.003,
                        cost_per_1k_output=0.015,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="claude-3-5-haiku-20241022",
                        display_name="Claude 3.5 Haiku",
                        context_window=200000,
                        max_output_tokens=8192,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.0008,
                        cost_per_1k_output=0.004,
                        is_recommended=False,
                    ),
                    # Claude 3 Series
                    ModelInfo(
                        id="claude-3-opus-20240229",
                        display_name="Claude 3 Opus",
                        context_window=200000,
                        max_output_tokens=4096,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.015,
                        cost_per_1k_output=0.075,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="claude-3-sonnet-20240229",
                        display_name="Claude 3 Sonnet",
                        context_window=200000,
                        max_output_tokens=4096,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.003,
                        cost_per_1k_output=0.015,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="claude-3-haiku-20240307",
                        display_name="Claude 3 Haiku",
                        context_window=200000,
                        max_output_tokens=4096,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.00025,
                        cost_per_1k_output=0.00125,
                        is_recommended=False,
                    ),
                ],
            )
        )

        # ═══════════════════════════════════════════════════════════════
        # OPENAI (GPT)
        # ═══════════════════════════════════════════════════════════════
        self.register_provider(
            ProviderConfig(
                name="openai",
                display_name="OpenAI (GPT)",
                prefix="openai/",
                api_key_env="OPENAI_API_KEY",
                fallback_env=None,
                models=[
                    # GPT-4o Series (Latest)
                    ModelInfo(
                        id="gpt-4o",
                        display_name="GPT-4o",
                        context_window=128000,
                        max_output_tokens=16384,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.005,
                        cost_per_1k_output=0.015,
                        is_recommended=True,
                    ),
                    ModelInfo(
                        id="gpt-4o-mini",
                        display_name="GPT-4o Mini",
                        context_window=128000,
                        max_output_tokens=16384,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.00015,
                        cost_per_1k_output=0.0006,
                        is_recommended=False,
                    ),
                    # GPT-4 Turbo
                    ModelInfo(
                        id="gpt-4-turbo",
                        display_name="GPT-4 Turbo",
                        context_window=128000,
                        max_output_tokens=4096,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.01,
                        cost_per_1k_output=0.03,
                        is_recommended=False,
                    ),
                    # GPT-4
                    ModelInfo(
                        id="gpt-4",
                        display_name="GPT-4",
                        context_window=8192,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.03,
                        cost_per_1k_output=0.06,
                        is_recommended=False,
                    ),
                    # GPT-3.5 Turbo
                    ModelInfo(
                        id="gpt-3.5-turbo",
                        display_name="GPT-3.5 Turbo",
                        context_window=16385,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.0005,
                        cost_per_1k_output=0.0015,
                        is_recommended=False,
                    ),
                    # O-series (Reasoning)
                    ModelInfo(
                        id="o1",
                        display_name="O1 (Reasoning)",
                        context_window=200000,
                        max_output_tokens=100000,
                        supports_vision=True,
                        supports_tools=False,
                        cost_per_1k_input=0.015,
                        cost_per_1k_output=0.06,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="o1-mini",
                        display_name="O1 Mini (Reasoning)",
                        context_window=128000,
                        max_output_tokens=65536,
                        supports_vision=False,
                        supports_tools=False,
                        cost_per_1k_input=0.003,
                        cost_per_1k_output=0.012,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="o3-mini",
                        display_name="O3 Mini (Reasoning)",
                        context_window=200000,
                        max_output_tokens=100000,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.00115,
                        cost_per_1k_output=0.0044,
                        is_recommended=False,
                    ),
                ],
            )
        )

        # ═══════════════════════════════════════════════════════════════
        # MISTRAL
        # ═══════════════════════════════════════════════════════════════
        self.register_provider(
            ProviderConfig(
                name="mistral",
                display_name="Mistral AI",
                prefix="mistral/",
                api_key_env="MISTRAL_API_KEY",
                fallback_env=None,
                models=[
                    # Large Models
                    ModelInfo(
                        id="mistral-large-latest",
                        display_name="Mistral Large",
                        context_window=128000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.002,
                        cost_per_1k_output=0.006,
                        is_recommended=True,
                    ),
                    ModelInfo(
                        id="mistral-large-2411",
                        display_name="Mistral Large (Nov 2024)",
                        context_window=128000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.002,
                        cost_per_1k_output=0.006,
                        is_recommended=False,
                    ),
                    # Medium Models
                    ModelInfo(
                        id="mistral-medium-latest",
                        display_name="Mistral Medium",
                        context_window=32000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.00275,
                        cost_per_1k_output=0.0081,
                        is_recommended=False,
                    ),
                    # Small Models
                    ModelInfo(
                        id="mistral-small-latest",
                        display_name="Mistral Small",
                        context_window=32000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.0002,
                        cost_per_1k_output=0.0006,
                        is_recommended=False,
                    ),
                    # Codestral (Code-focused)
                    ModelInfo(
                        id="codestral-latest",
                        display_name="Codestral (Code)",
                        context_window=32000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.0002,
                        cost_per_1k_output=0.0006,
                        is_recommended=False,
                    ),
                    # Open Source Models
                    ModelInfo(
                        id="open-mixtral-8x22b",
                        display_name="Mixtral 8x22B",
                        context_window=65536,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.002,
                        cost_per_1k_output=0.006,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="open-mixtral-8x7b",
                        display_name="Mixtral 8x7B",
                        context_window=32000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.0007,
                        cost_per_1k_output=0.0007,
                        is_recommended=False,
                    ),
                    ModelInfo(
                        id="open-mistral-nemo",
                        display_name="Mistral NeMo",
                        context_window=128000,
                        max_output_tokens=4096,
                        supports_vision=False,
                        supports_tools=True,
                        cost_per_1k_input=0.00015,
                        cost_per_1k_output=0.00015,
                        is_recommended=False,
                    ),
                    # Pixtral (Vision)
                    ModelInfo(
                        id="pixtral-large-latest",
                        display_name="Pixtral Large (Vision)",
                        context_window=128000,
                        max_output_tokens=4096,
                        supports_vision=True,
                        supports_tools=True,
                        cost_per_1k_input=0.002,
                        cost_per_1k_output=0.006,
                        is_recommended=False,
                    ),
                ],
            )
        )

        logger.info(
            f"ProviderRegistry initialized with {len(self._providers)} providers: "
            f"{', '.join(self._providers.keys())}"
        )

    def register_provider(self, config: ProviderConfig) -> None:
        """Register a provider configuration."""
        self._providers[config.name] = config
        logger.debug(f"Registered provider: {config.name} with {len(config.models)} models")

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get provider config by name."""
        return self._providers.get(name)

    def list_providers(self) -> List[ProviderInfo]:
        """
        List all providers with availability status.

        SECURITY: Never exposes API key values, only is_configured boolean.

        Returns:
            List of ProviderInfo with is_configured based on env var check.
        """
        providers = []
        for config in self._providers.values():
            is_configured = config.is_configured
            status = "available" if is_configured else "not_configured"

            providers.append(
                ProviderInfo(
                    name=config.name,
                    display_name=config.display_name,
                    prefix=config.prefix,
                    is_configured=is_configured,
                    status=status,
                    models=config.models,
                )
            )

        # Sort by: configured first, then alphabetically
        providers.sort(key=lambda p: (not p.is_configured, p.name))
        return providers

    def get_api_key(self, provider_name: str) -> Optional[str]:
        """
        Get API key for provider from environment.

        SECURITY: API keys are ONLY read from environment variables.
        They are NEVER stored in the database.
        """
        config = self.get_provider(provider_name)
        if config:
            return config.get_api_key()
        return None

    def is_provider_configured(self, provider_name: str) -> bool:
        """Check if provider API key exists in environment."""
        config = self.get_provider(provider_name)
        return config.is_configured if config else False

    def get_model_ids(self, provider_name: str) -> List[str]:
        """Get list of valid model IDs for a provider."""
        config = self.get_provider(provider_name)
        if config:
            return [m.id for m in config.models]
        return []


# Global singleton instance
provider_registry = ProviderRegistry()
