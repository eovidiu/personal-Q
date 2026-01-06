"""
Integration tests for PERSONAL_Q_API_KEY configuration feature.

Tests the environment-based API key configuration:
- get_anthropic_api_key() function in llm_service.py
- /api-key-status endpoint in settings.py
- CrewService behavior with/without API key
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


class TestCrewServiceApiKeyHandling:
    """Integration tests for CrewService API key handling."""

    @pytest.mark.asyncio
    async def test_crew_service_fails_gracefully_without_api_key(self):
        """Test CrewService returns error dict when API key not configured."""
        from app.services.crew_service import CrewService, CREWAI_AVAILABLE
        from app.models.agent import Agent, AgentType, AgentStatus

        if not CREWAI_AVAILABLE:
            pytest.skip("CrewAI not available")

        # Mock get_anthropic_api_key to raise ValueError
        with patch("app.services.crew_service.get_anthropic_api_key") as mock_get_key:
            mock_get_key.side_effect = ValueError(
                "PERSONAL_Q_API_KEY environment variable is not set. "
                "This is required for agent execution."
            )

            agent = Agent(
                id="test-agent-no-key",
                name="Test Agent",
                description="Test agent for API key failure",
                agent_type=AgentType.CONVERSATIONAL,
                model="claude-3-5-sonnet-20241022",
                system_prompt="You are a test agent.",
                temperature=0.7,
                max_tokens=2048,
                status=AgentStatus.ACTIVE,
            )

            mock_db = Mock()
            result = await CrewService.execute_agent_task(
                db=mock_db,
                agent=agent,
                task_description="Test task that should fail",
            )

            # Verify graceful failure
            assert result["success"] is False
            assert "PERSONAL_Q_API_KEY" in result["error"]
            assert "not set" in result["error"]
            assert result["agent_id"] == "test-agent-no-key"

    @pytest.mark.asyncio
    async def test_crew_service_multi_agent_fails_gracefully_without_api_key(self):
        """Test CrewService multi-agent returns error when API key not configured."""
        from app.services.crew_service import CrewService, CREWAI_AVAILABLE
        from app.models.agent import Agent, AgentType, AgentStatus

        if not CREWAI_AVAILABLE:
            pytest.skip("CrewAI not available")

        with patch("app.services.crew_service.get_anthropic_api_key") as mock_get_key:
            mock_get_key.side_effect = ValueError(
                "PERSONAL_Q_API_KEY environment variable is not set."
            )

            agents = [
                Agent(
                    id="agent-1",
                    name="Agent 1",
                    description="First test agent",
                    agent_type=AgentType.ANALYTICAL,
                    model="claude-3-5-sonnet-20241022",
                    system_prompt="Test agent 1",
                    temperature=0.7,
                    max_tokens=2048,
                    status=AgentStatus.ACTIVE,
                ),
                Agent(
                    id="agent-2",
                    name="Agent 2",
                    description="Second test agent",
                    agent_type=AgentType.CREATIVE,
                    model="claude-3-5-sonnet-20241022",
                    system_prompt="Test agent 2",
                    temperature=0.8,
                    max_tokens=2048,
                    status=AgentStatus.ACTIVE,
                ),
            ]

            mock_db = Mock()
            result = await CrewService.execute_multi_agent_task(
                db=mock_db,
                agents=agents,
                task_descriptions=["Task 1", "Task 2"],
            )

            # Verify graceful failure
            assert result["success"] is False
            assert "PERSONAL_Q_API_KEY" in result["error"]
            assert len(result["agents"]) == 2

    @pytest.mark.asyncio
    async def test_crew_service_error_message_content(self):
        """Test that CrewService error message provides actionable information."""
        from app.services.crew_service import CrewService, CREWAI_AVAILABLE
        from app.models.agent import Agent, AgentType, AgentStatus

        if not CREWAI_AVAILABLE:
            pytest.skip("CrewAI not available")

        with patch("app.services.crew_service.get_anthropic_api_key") as mock_get_key:
            error_message = (
                "PERSONAL_Q_API_KEY environment variable is not set. "
                "This is required for agent execution."
            )
            mock_get_key.side_effect = ValueError(error_message)

            agent = Agent(
                id="test-agent",
                name="Test Agent",
                description="Test",
                agent_type=AgentType.CONVERSATIONAL,
                model="claude-3-5-sonnet-20241022",
                system_prompt="Test",
                temperature=0.7,
                max_tokens=2048,
                status=AgentStatus.ACTIVE,
            )

            mock_db = Mock()
            result = await CrewService.execute_agent_task(
                db=mock_db,
                agent=agent,
                task_description="Test task",
            )

            # Error message should be actionable
            assert "PERSONAL_Q_API_KEY" in result["error"]
            assert "required" in result["error"]


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
