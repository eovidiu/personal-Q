"""
ABOUTME: Pydantic schemas for LLM provider and model information.
ABOUTME: Used by the /api/v1/llm/providers endpoint to return available providers.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Information about a specific LLM model."""

    id: str = Field(..., description="Model identifier (e.g., 'claude-3-5-sonnet-20241022')")
    display_name: str = Field(..., description="Human-readable name")
    context_window: int = Field(..., description="Maximum context tokens")
    max_output_tokens: int = Field(default=4096, description="Maximum output tokens")
    supports_vision: bool = Field(default=False, description="Supports image input")
    supports_tools: bool = Field(default=True, description="Supports function calling")
    cost_per_1k_input: float = Field(..., description="Cost per 1K input tokens (USD)")
    cost_per_1k_output: float = Field(..., description="Cost per 1K output tokens (USD)")
    is_recommended: bool = Field(default=False, description="Recommended model for this provider")


class ProviderInfo(BaseModel):
    """Information about an LLM provider."""

    name: str = Field(..., description="Provider identifier (e.g., 'anthropic', 'openai')")
    display_name: str = Field(..., description="Human-readable name (e.g., 'Anthropic (Claude)')")
    prefix: str = Field(..., description="LiteLLM prefix (e.g., 'anthropic/')")
    is_configured: bool = Field(..., description="Whether API key is configured in environment")
    status: str = Field(..., description="'available', 'not_configured', or 'error'")
    models: List[ModelInfo] = Field(default_factory=list, description="Available models")


class ProvidersResponse(BaseModel):
    """Response schema for GET /api/v1/llm/providers."""

    providers: List[ProviderInfo] = Field(..., description="List of available providers")
    default_provider: str = Field(..., description="Default provider name")
    default_model: str = Field(..., description="Default model (full format with prefix)")


class ValidationResult(BaseModel):
    """Result of model string validation."""

    is_valid: bool = Field(..., description="Whether the model string is valid")
    provider: Optional[str] = Field(None, description="Parsed provider name")
    model: Optional[str] = Field(None, description="Parsed model identifier")
    normalized: Optional[str] = Field(None, description="Normalized model string (provider/model)")
    error: Optional[str] = Field(None, description="Error message if invalid")
