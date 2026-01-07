"""
ABOUTME: LLM provider and model management API endpoints.
ABOUTME: Provides provider enumeration for frontend model selection dropdown.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.schemas.llm import ProvidersResponse, ValidationResult
from app.services.model_validator import model_validator
from app.services.provider_registry import provider_registry
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers(
    current_user: Dict = Depends(get_current_user),
) -> ProvidersResponse:
    """
    List available LLM providers and their models.

    Returns providers with configuration status and available models.
    Providers with configured API keys are listed first.

    **Authentication**: Required

    **Returns**:
    - providers: List of ProviderInfo with models
    - default_provider: Name of default provider (first configured)
    - default_model: Full model string (e.g., "anthropic/claude-3-5-sonnet-20241022")

    **Security**:
    - API keys are NEVER exposed in responses
    - Only `is_configured: bool` indicates key availability
    """
    providers_info = provider_registry.list_providers()

    # Determine default provider (first configured provider)
    default_provider = "anthropic"  # Fallback
    for provider in providers_info:
        if provider.is_configured:
            default_provider = provider.name
            break

    # Get default model from settings, ensure it has provider prefix
    default_model = settings.default_model
    if "/" not in default_model:
        default_model = f"anthropic/{default_model}"

    logger.debug(
        f"Listing {len(providers_info)} providers, "
        f"{sum(1 for p in providers_info if p.is_configured)} configured"
    )

    return ProvidersResponse(
        providers=providers_info,
        default_provider=default_provider,
        default_model=default_model,
    )


@router.get("/validate/{model:path}", response_model=ValidationResult)
async def validate_model(
    model: str,
    check_configured: bool = True,
    current_user: Dict = Depends(get_current_user),
) -> ValidationResult:
    """
    Validate a model string.

    Checks if the model string is valid and the provider is configured.

    **Authentication**: Required

    **Path Parameters**:
    - model: Model string to validate (e.g., "anthropic/claude-3-5-sonnet-20241022")

    **Query Parameters**:
    - check_configured: Whether to verify API key is configured (default: true)

    **Returns**:
    - is_valid: Whether the model string is valid
    - provider: Parsed provider name
    - model: Parsed model identifier
    - normalized: Normalized model string
    - error: Error message if invalid
    """
    result = model_validator.validate_model(model, check_configured=check_configured)
    return result
