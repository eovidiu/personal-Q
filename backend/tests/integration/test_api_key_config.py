"""
Integration tests for PERSONAL_Q_API_KEY configuration feature.

Tests the environment-based API key configuration:
- get_anthropic_api_key() function in llm_service.py
- /api-key-status endpoint in settings.py
- AgentRuntime behavior with/without API key
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport


class TestGetAnthropicApiKey:
    """Unit tests for get_anthropic_api_key() function."""

    def test_get_api_key_returns_env_var_when_set(self):
        """Test that get_anthropic_api_key returns the env var value when set."""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.personal_q_api_key = "sk-ant-test-key-123"

            from app.services.llm_service import get_anthropic_api_key

            result = get_anthropic_api_key()

            assert result == "sk-ant-test-key-123"

    def test_get_api_key_raises_when_not_set(self):
        """Test that get_anthropic_api_key raises ValueError when env var not set."""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.personal_q_api_key = None

            from app.services.llm_service import get_anthropic_api_key

            with pytest.raises(ValueError) as exc_info:
                get_anthropic_api_key()

            assert "PERSONAL_Q_API_KEY environment variable is not set" in str(exc_info.value)
            assert "required for agent execution" in str(exc_info.value)

    def test_get_api_key_raises_when_empty_string(self):
        """Test that get_anthropic_api_key raises ValueError when env var is empty."""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.personal_q_api_key = ""

            from app.services.llm_service import get_anthropic_api_key

            with pytest.raises(ValueError) as exc_info:
                get_anthropic_api_key()

            assert "PERSONAL_Q_API_KEY" in str(exc_info.value)


class TestApiKeyStatusEndpoint:
    """Integration tests for /api-key-status endpoint."""

    @pytest.mark.asyncio
    async def test_api_key_status_endpoint_configured(self, test_app):
        """Test /api-key-status returns configured=True when env var is set."""
        # Patch the settings object where it's imported in the endpoint function
        with patch("config.settings.settings") as mock_settings:
            mock_settings.personal_q_api_key = "sk-ant-configured-key"

            transport = ASGITransport(app=test_app)
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=True
            ) as client:
                response = await client.get("/api/v1/settings/api-key-status")

        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["variable_name"] == "PERSONAL_Q_API_KEY"
        assert "configured via environment variable" in data["message"]

    @pytest.mark.asyncio
    async def test_api_key_status_endpoint_not_configured(self, test_app):
        """Test /api-key-status returns configured=False when env var not set."""
        with patch("config.settings.settings") as mock_settings:
            mock_settings.personal_q_api_key = None

            transport = ASGITransport(app=test_app)
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=True
            ) as client:
                response = await client.get("/api/v1/settings/api-key-status")

        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert "not set" in data["message"]

    @pytest.mark.asyncio
    async def test_api_key_status_endpoint_empty_string(self, test_app):
        """Test /api-key-status returns configured=False when env var is empty string."""
        with patch("config.settings.settings") as mock_settings:
            mock_settings.personal_q_api_key = ""

            transport = ASGITransport(app=test_app)
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=True
            ) as client:
                response = await client.get("/api/v1/settings/api-key-status")

        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False


class TestAgentRuntimeApiKeyHandling:
    """Integration tests for AgentRuntime API key handling."""

    @staticmethod
    def _make_agent(**overrides):
        from app.models.agent import Agent, AgentType, AgentStatus

        defaults = dict(
            id="test-agent-no-key",
            name="Test Agent",
            description="Test agent for API key failure",
            agent_type=AgentType.CONVERSATIONAL,
            model="anthropic/claude-opus-4-8",
            system_prompt="You are a test agent.",
            temperature=0.7,
            max_tokens=2048,
            status=AgentStatus.ACTIVE,
        )
        defaults.update(overrides)
        return Agent(**defaults)

    @pytest.mark.asyncio
    async def test_agent_runtime_fails_gracefully_without_api_key(self):
        """AgentRuntime returns an error dict when no Anthropic API key is configured."""
        from app.services.agent_runtime import AgentRuntime
        from app.schemas.llm import ValidationResult

        agent = self._make_agent()

        # Model validates as a configured Anthropic model, but the key lookup
        # returns None — exercising the runtime's explicit "key missing" branch.
        with patch(
            "app.services.agent_runtime.model_validator.validate_model",
            return_value=ValidationResult(
                is_valid=True,
                provider="anthropic",
                model="claude-opus-4-8",
                normalized="anthropic/claude-opus-4-8",
            ),
        ), patch(
            "app.services.agent_runtime.provider_registry.get_api_key",
            return_value=None,
        ):
            result = await AgentRuntime.execute_agent_task(
                db=Mock(),
                agent=agent,
                task_description="Test task that should fail",
            )

        assert result["success"] is False
        assert "anthropic" in result["error"].lower()
        assert "api key" in result["error"].lower()
        assert result["agent_id"] == "test-agent-no-key"

    @pytest.mark.asyncio
    async def test_agent_runtime_rejects_non_anthropic_provider(self):
        """AgentRuntime returns a clear error for non-Anthropic providers."""
        from app.services.agent_runtime import AgentRuntime
        from app.schemas.llm import ValidationResult

        agent = self._make_agent(model="openai/gpt-4o")

        with patch(
            "app.services.agent_runtime.model_validator.validate_model",
            return_value=ValidationResult(
                is_valid=True,
                provider="openai",
                model="gpt-4o",
                normalized="openai/gpt-4o",
            ),
        ):
            result = await AgentRuntime.execute_agent_task(
                db=Mock(),
                agent=agent,
                task_description="Test task",
            )

        assert result["success"] is False
        assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_agent_runtime_multi_agent_fails_gracefully_without_api_key(self):
        """Multi-agent execution returns an error when the API key is missing."""
        from app.services.agent_runtime import AgentRuntime
        from app.schemas.llm import ValidationResult

        agents = [
            self._make_agent(id="agent-1", name="Agent 1"),
            self._make_agent(id="agent-2", name="Agent 2"),
        ]

        with patch(
            "app.services.agent_runtime.model_validator.validate_model",
            return_value=ValidationResult(
                is_valid=True,
                provider="anthropic",
                model="claude-opus-4-8",
                normalized="anthropic/claude-opus-4-8",
            ),
        ), patch(
            "app.services.agent_runtime.provider_registry.get_api_key",
            return_value=None,
        ):
            result = await AgentRuntime.execute_multi_agent_task(
                db=Mock(),
                agents=agents,
                task_descriptions=["Task 1", "Task 2"],
            )

        assert result["success"] is False
        assert "api key" in result["error"].lower()
        assert result["failed_agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_agent_runtime_multi_agent_task_count_mismatch(self):
        """Mismatched agent/task counts raise ValueError."""
        from app.services.agent_runtime import AgentRuntime

        agents = [self._make_agent(id="agent-1", name="Agent 1")]

        with pytest.raises(ValueError, match="Number of agents must match number of tasks"):
            await AgentRuntime.execute_multi_agent_task(
                db=Mock(),
                agents=agents,
                task_descriptions=["Task 1", "Task 2"],
            )


class TestApiKeyConfigIntegration:
    """End-to-end integration tests for API key configuration."""

    @pytest.mark.asyncio
    async def test_api_key_workflow_not_configured(self, test_app):
        """Test full workflow when API key is not configured."""
        with patch("config.settings.settings") as mock_settings:
            mock_settings.personal_q_api_key = None

            transport = ASGITransport(app=test_app)
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=True
            ) as client:
                # Step 1: Check status - should show not configured
                status_response = await client.get("/api/v1/settings/api-key-status")

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["configured"] is False

    @pytest.mark.asyncio
    async def test_api_key_workflow_configured(self, test_app):
        """Test full workflow when API key is configured."""
        with patch("config.settings.settings") as mock_settings:
            mock_settings.personal_q_api_key = "sk-ant-valid-key"

            transport = ASGITransport(app=test_app)
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=True
            ) as client:
                # Step 1: Check status - should show configured
                status_response = await client.get("/api/v1/settings/api-key-status")

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["configured"] is True
        assert status_data["variable_name"] == "PERSONAL_Q_API_KEY"
