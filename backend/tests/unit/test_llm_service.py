"""
Unit tests for LLM service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.llm_service import LLMService


class TestLLMService:
    """Tests for LLM Service."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        service = LLMService()
        assert service.api_key is None

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        service = LLMService(api_key="test-key")
        assert service.api_key == "test-key"

    def test_set_api_key(self):
        """Test setting API key."""
        service = LLMService()
        service.set_api_key("new-key")
        assert service.api_key == "new-key"

    def test_client_property_without_key_raises_error(self):
        """Test accessing client without API key raises error."""
        service = LLMService()
        with pytest.raises(ValueError, match="API key not set"):
            _ = service.client

    def test_estimate_tokens(self):
        """Test token estimation."""
        service = LLMService()
        text = "This is a test message with approximately twenty tokens here."
        tokens = service.estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_cost(self):
        """Test cost estimation."""
        service = LLMService()
        cost = service.estimate_cost(
            input_tokens=1000,
            output_tokens=500,
            model="claude-3-5-sonnet-20241022"
        )
        assert cost > 0
        assert isinstance(cost, float)

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation with unknown model uses default."""
        service = LLMService()
        cost = service.estimate_cost(
            input_tokens=1000,
            output_tokens=500,
            model="unknown-model"
        )
        assert cost > 0

    @pytest.mark.asyncio
    async def test_generate_without_api_key_raises_error(self):
        """Test generate without API key raises error."""
        service = LLMService()
        with pytest.raises(ValueError, match="API key not set"):
            await service.generate("test prompt")

    @pytest.mark.asyncio
    @patch("app.services.llm_service.AsyncAnthropic")
    async def test_generate_success(self, mock_anthropic):
        """Test successful generation."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_response.id = "test-id"

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        result = await service.generate("test prompt")

        assert result["success"] == True
        assert result["content"] == "Test response"
        assert result["model"] == "claude-3-5-sonnet-20241022"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 20
