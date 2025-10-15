"""
ABOUTME: LLM service for Claude integration with comprehensive resilience features.
ABOUTME: Includes timeouts, retries with exponential backoff, and circuit breakers.
"""

import httpx
import logging
from anthropic import Anthropic, AsyncAnthropic, APIError, APIConnectionError, RateLimitError
from typing import Optional, Dict, Any, AsyncIterator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from config.settings import settings

logger = logging.getLogger(__name__)

# Configure circuit breaker for LLM calls
# Opens after 5 failures, stays open for 60s
llm_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name="llm_service")


class LLMService:
    """Service for LLM operations using Claude with resilience features."""

    # Timeout configuration (in seconds)
    TIMEOUT_CONNECT = 5.0
    TIMEOUT_READ = 30.0
    TIMEOUT_TOTAL = 35.0

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
        """Get synchronous Anthropic client with timeout."""
        if not self.api_key:
            raise ValueError("API key not set. Configure in Settings.")

        if self._client is None:
            # Create httpx client with timeout configuration
            http_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=self.TIMEOUT_CONNECT, read=self.TIMEOUT_READ, write=10.0, pool=5.0
                )
            )
            self._client = Anthropic(api_key=self.api_key, http_client=http_client)

        return self._client

    @property
    def async_client(self) -> AsyncAnthropic:
        """Get asynchronous Anthropic client with timeout."""
        if not self.api_key:
            raise ValueError("API key not set. Configure in Settings.")

        if self._async_client is None:
            # Create httpx async client with timeout configuration
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.TIMEOUT_CONNECT, read=self.TIMEOUT_READ, write=10.0, pool=5.0
                )
            )
            self._async_client = AsyncAnthropic(api_key=self.api_key, http_client=http_client)

        return self._async_client

    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )
    @llm_breaker
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate completion using Claude with retries and circuit breaker.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt for agent behavior
            model: Model to use (default from settings)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Claude API

        Returns:
            Dictionary with response and metadata

        Raises:
            CircuitBreakerError: If circuit breaker is open
            APIError: If API request fails after retries
            httpx.TimeoutException: If request times out
        """
        model = model or settings.default_model
        temperature = temperature if temperature is not None else settings.default_temperature
        max_tokens = max_tokens or settings.default_max_tokens

        try:
            logger.debug(
                f"Generating with model {model}, temp={temperature}, max_tokens={max_tokens}"
            )

            response = await self.async_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            logger.info(
                f"LLM generation successful: {response.usage.input_tokens} in, {response.usage.output_tokens} out"
            )

            return {
                "content": response.content[0].text,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "id": response.id,
            }

        except RateLimitError as e:
            logger.warning(f"Rate limit hit, will retry: {e}")
            raise
        except APIConnectionError as e:
            logger.warning(f"Connection error, will retry: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout after {self.TIMEOUT_TOTAL}s, will retry: {e}")
            raise
        except APIError as e:
            logger.error(f"API error (non-retryable): {e}")
            raise RuntimeError(f"LLM generation failed: {str(e)}")
        except CircuitBreakerError:
            logger.error("Circuit breaker is OPEN - too many failures")
            raise RuntimeError("LLM service temporarily unavailable due to repeated failures")
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}", exc_info=True)
            raise RuntimeError(f"LLM generation failed: {str(e)}")

    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    @llm_breaker
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion using Claude with retries and circuit breaker.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Text chunks as they arrive

        Raises:
            CircuitBreakerError: If circuit breaker is open
            APIError: If API request fails
        """
        model = model or settings.default_model
        temperature = temperature if temperature is not None else settings.default_temperature
        max_tokens = max_tokens or settings.default_max_tokens

        try:
            logger.debug(f"Streaming with model {model}")

            async with self.async_client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except CircuitBreakerError:
            logger.error("Circuit breaker is OPEN - too many failures")
            raise RuntimeError("LLM service temporarily unavailable")
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}", exc_info=True)
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
            test_client = AsyncAnthropic(
                api_key=api_key,
                http_client=httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=10.0)),
            )
            # Make a minimal test request
            response = await test_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
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

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = None) -> float:
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

    def get_circuit_breaker_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state.

        Returns:
            Dictionary with circuit breaker metrics
        """
        return {
            "name": llm_breaker.name,
            "state": llm_breaker.current_state,
            "fail_counter": llm_breaker.fail_counter,
            "fail_max": llm_breaker.fail_max,
            "reset_timeout": llm_breaker.reset_timeout,
            "is_open": llm_breaker.current_state == "open",
        }


# Global LLM service instance
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return llm_service
