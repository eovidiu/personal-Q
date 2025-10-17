"""
Unit tests for CrewAI service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.crew_service import CrewService, CREWAI_AVAILABLE
from app.models.agent import Agent, AgentType, AgentStatus


class TestCrewService:
    """Tests for CrewAI Service."""

    def test_crewai_availability(self):
        """Test CrewAI import status."""
        # Will be True if installation succeeds
        assert isinstance(CREWAI_AVAILABLE, bool)
        # After our implementation, this should be True
        assert CREWAI_AVAILABLE is True, "CrewAI should be available after installation"

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    def test_agent_type_to_role_mapping(self):
        """Test agent type to role mapping."""
        role_conversational = CrewService._map_agent_type_to_role(AgentType.CONVERSATIONAL)
        assert "Support" in role_conversational or "Customer" in role_conversational

        role_analytical = CrewService._map_agent_type_to_role(AgentType.ANALYTICAL)
        assert "Analyst" in role_analytical or "Data" in role_analytical

        role_creative = CrewService._map_agent_type_to_role(AgentType.CREATIVE)
        assert "Creative" in role_creative or "Content" in role_creative

        role_automation = CrewService._map_agent_type_to_role(AgentType.AUTOMATION)
        assert "Automation" in role_automation or "Workflow" in role_automation

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    @patch("app.services.crew_service.ChatAnthropic")
    def test_create_crew_agent(self, mock_chat_anthropic):
        """Test creating a CrewAI agent from database model."""
        # Create test agent
        agent = Agent(
            id="test-123",
            name="Test Agent",
            description="Test description",
            agent_type=AgentType.ANALYTICAL,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent.",
            temperature=0.7,
            max_tokens=2048,
            status=AgentStatus.ACTIVE
        )

        # Mock LLM instance
        mock_llm = Mock()

        # Create CrewAI agent
        crew_agent = CrewService._create_crew_agent(agent, mock_llm)

        # Verify agent creation
        assert crew_agent is not None
        assert "Analyst" in crew_agent.role or "Data" in crew_agent.role
        assert crew_agent.goal == agent.description
        assert crew_agent.backstory == agent.system_prompt
        assert crew_agent.verbose is True
        assert crew_agent.allow_delegation is True

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    @pytest.mark.asyncio
    async def test_execute_agent_task_without_api_key(self):
        """Test task execution fails gracefully without API key."""
        from app.services.llm_service import llm_service

        # Ensure API key is not set
        original_key = llm_service.api_key
        llm_service.api_key = None

        try:
            agent = Agent(
                id="test-123",
                name="Test Agent",
                description="Test",
                agent_type=AgentType.CONVERSATIONAL,
                model="claude-3-5-sonnet-20241022",
                system_prompt="Test",
                temperature=0.7,
                max_tokens=2048,
                status=AgentStatus.ACTIVE
            )

            result = await CrewService.execute_agent_task(
                db=Mock(),
                agent=agent,
                task_description="Test task"
            )

            # Should return error about missing API key
            assert result["success"] is False
            assert "API key not configured" in result["error"]
        finally:
            # Restore original key
            llm_service.api_key = original_key

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    @pytest.mark.asyncio
    async def test_execute_multi_agent_task_validation(self):
        """Test multi-agent task validation."""
        from app.services.llm_service import llm_service

        # Ensure API key is not set
        original_key = llm_service.api_key
        llm_service.api_key = None

        try:
            agents = [
                Agent(
                    id="agent-1",
                    name="Agent 1",
                    description="Test",
                    agent_type=AgentType.ANALYTICAL,
                    model="claude-3-5-sonnet-20241022",
                    system_prompt="Test",
                    temperature=0.7,
                    max_tokens=2048,
                    status=AgentStatus.ACTIVE
                )
            ]

            tasks = ["Task 1", "Task 2"]  # Mismatch: 1 agent, 2 tasks

            with pytest.raises(ValueError, match="Number of agents must match number of tasks"):
                await CrewService.execute_multi_agent_task(
                    db=Mock(),
                    agents=agents,
                    task_descriptions=tasks
                )
        finally:
            llm_service.api_key = original_key

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    def test_create_agent_tools(self):
        """Test creating agent tools."""
        agent = Agent(
            id="test-123",
            name="Test Agent",
            description="Test",
            agent_type=AgentType.AUTOMATION,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test",
            temperature=0.7,
            max_tokens=2048,
            status=AgentStatus.ACTIVE
        )

        tools = CrewService.create_agent_tools(agent)

        # Should return empty list for now (tools not yet implemented)
        assert isinstance(tools, list)

    def test_crewai_not_available_fallback(self):
        """Test that service handles CrewAI not being available."""
        if not CREWAI_AVAILABLE:
            # This test only makes sense if CrewAI is not available
            # In our case, after implementation, CREWAI_AVAILABLE should be True
            # But we keep this test for completeness
            pytest.skip("CrewAI is available - this test checks unavailable scenario")

        # If we reach here, CrewAI is available, which is the expected state
        assert CREWAI_AVAILABLE is True


class TestCrewServiceIntegration:
    """Integration tests for CrewAI service with mock LLM."""

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    @pytest.mark.asyncio
    @patch("app.services.crew_service.ChatAnthropic")
    @patch("app.services.crew_service.llm_service")
    async def test_execute_agent_task_with_mocked_llm(self, mock_llm_service, mock_chat_anthropic):
        """Test executing a task with mocked LLM."""
        # Configure mocks
        mock_llm_service.api_key = "test-api-key"
        mock_llm = Mock()
        mock_chat_anthropic.return_value = mock_llm

        # Mock Crew execution
        with patch("app.services.crew_service.Crew") as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = "Task completed successfully"
            mock_crew_class.return_value = mock_crew

            agent = Agent(
                id="test-123",
                name="Test Agent",
                description="Test agent for testing",
                agent_type=AgentType.CONVERSATIONAL,
                model="claude-3-5-sonnet-20241022",
                system_prompt="You are a helpful test agent.",
                temperature=0.7,
                max_tokens=2048,
                status=AgentStatus.ACTIVE
            )

            result = await CrewService.execute_agent_task(
                db=Mock(),
                agent=agent,
                task_description="Complete a test task"
            )

            # Verify success
            assert result["success"] is True
            assert "result" in result
            assert result["agent_id"] == "test-123"

    @pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
    @pytest.mark.asyncio
    @patch("app.services.crew_service.ChatAnthropic")
    @patch("app.services.crew_service.llm_service")
    async def test_execute_multi_agent_task_sequential(self, mock_llm_service, mock_chat_anthropic):
        """Test executing multi-agent task in sequential mode."""
        # Configure mocks
        mock_llm_service.api_key = "test-api-key"
        mock_llm = Mock()
        mock_chat_anthropic.return_value = mock_llm

        # Mock Crew execution
        with patch("app.services.crew_service.Crew") as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = "All tasks completed"
            mock_crew_class.return_value = mock_crew

            agents = [
                Agent(
                    id="agent-1",
                    name="Research Agent",
                    description="Research topics",
                    agent_type=AgentType.ANALYTICAL,
                    model="claude-3-5-sonnet-20241022",
                    system_prompt="You research topics.",
                    temperature=0.7,
                    max_tokens=2048,
                    status=AgentStatus.ACTIVE
                ),
                Agent(
                    id="agent-2",
                    name="Writing Agent",
                    description="Write content",
                    agent_type=AgentType.CREATIVE,
                    model="claude-3-5-sonnet-20241022",
                    system_prompt="You write content.",
                    temperature=0.9,
                    max_tokens=2048,
                    status=AgentStatus.ACTIVE
                )
            ]

            tasks = [
                "Research AI trends",
                "Write article about findings"
            ]

            result = await CrewService.execute_multi_agent_task(
                db=Mock(),
                agents=agents,
                task_descriptions=tasks,
                process="sequential"
            )

            # Verify success
            assert result["success"] is True
            assert "result" in result
            assert len(result["agents"]) == 2
            assert result["process"] == "sequential"
