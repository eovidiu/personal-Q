"""
LLM service for Claude integration.
"""

from anthropic import Anthropic, AsyncAnthropic
from typing import Optional, Dict, Any, AsyncIterator
import sys

sys.path.insert(0, "/root/repo/backend")

from config.settings import settings


class LLMService:
    """Service for LLM operations using Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            api_key: Anthropic API key (if None, will need to be set later)
        """
        self.api_key = api_key
        self._client = None
        self._async_client = None

    def set_api_key(self, api_key: str):
        """Set or update API key."""
        self.api_key = api_key
        self._client = None
        self._async_client = None

    @property
    def client(self) -> Anthropic:
        """Get synchronous Anthropic client."""
        if not self.api_key:
            raise ValueError("API key not set. Configure in Settings.")

        if self._client is None:
            self._client = Anthropic(api_key=self.api_key)

        return self._client

    @property
    def async_client(self) -> AsyncAnthropic:
        """Get asynchronous Anthropic client."""
        if not self.api_key:
            raise ValueError("API key not set. Configure in Settings.")

        if self._async_client is None:
            self._async_client = AsyncAnthropic(api_key=self.api_key)

        return self._async_client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using Claude.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt for agent behavior
            model: Model to use (default from settings)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Claude API

        Returns:
            Dictionary with response and metadata
        """
        model = model or settings.default_model
        temperature = temperature if temperature is not None else settings.default_temperature
        max_tokens = max_tokens or settings.default_max_tokens

        try:
            response = await self.async_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )

            return {
                "content": response.content[0].text,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "id": response.id
            }

        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion using Claude.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Text chunks as they arrive
        """
        model = model or settings.default_model
        temperature = temperature if temperature is not None else settings.default_temperature
        max_tokens = max_tokens or settings.default_max_tokens

        try:
            async with self.async_client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            raise RuntimeError(f"LLM streaming failed: {str(e)}")

    async def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key by making a test request.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            test_client = AsyncAnthropic(api_key=api_key)
            # Make a minimal test request
            response = await test_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Rough estimation: ~4 characters per token for English text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = None
    ) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model used

        Returns:
            Estimated cost in USD
        """
        model = model or settings.default_model

        # Pricing as of 2024 (per million tokens)
        pricing = {
            "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }

        rates = pricing.get(model, {"input": 3.00, "output": 15.00})

        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost


# Global LLM service instance
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return llm_service
