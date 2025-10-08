"""
Unit tests for Agent service.
"""

import pytest
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, AgentUpdate, AgentStatusUpdate
from app.models.agent import AgentType, AgentStatus


class TestAgentService:
    """Tests for AgentService."""

    @pytest.mark.asyncio
    async def test_create_agent(self, test_session):
        """Test creating an agent."""
        agent_data = AgentCreate(
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CONVERSATIONAL,
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            system_prompt="You are a test agent.",
            tags=["test"]
        )

        agent = await AgentService.create_agent(test_session, agent_data)

        assert agent is not None
        assert agent.id is not None
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.CONVERSATIONAL
        assert agent.status == AgentStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_create_agent_duplicate_name(self, test_session):
        """Test creating agent with duplicate name fails."""
        agent_data = AgentCreate(
            name="Duplicate Agent",
            description="A test agent",
            agent_type=AgentType.ANALYTICAL,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent."
        )

        # Create first agent
        await AgentService.create_agent(test_session, agent_data)

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await AgentService.create_agent(test_session, agent_data)

    @pytest.mark.asyncio
    async def test_get_agent(self, test_session):
        """Test getting an agent by ID."""
        # Create agent first
        agent_data = AgentCreate(
            name="Get Test Agent",
            description="A test agent",
            agent_type=AgentType.CREATIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent."
        )
        created_agent = await AgentService.create_agent(test_session, agent_data)

        # Get agent
        agent = await AgentService.get_agent(test_session, created_agent.id)

        assert agent is not None
        assert agent.id == created_agent.id
        assert agent.name == "Get Test Agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, test_session):
        """Test getting non-existent agent returns None."""
        agent = await AgentService.get_agent(test_session, str(uuid.uuid4()))
        assert agent is None

    @pytest.mark.asyncio
    async def test_list_agents(self, test_session):
        """Test listing agents."""
        # Create multiple agents
        for i in range(5):
            agent_data = AgentCreate(
                name=f"List Agent {i}",
                description=f"Agent {i}",
                agent_type=AgentType.CONVERSATIONAL,
                model="claude-3-5-sonnet-20241022",
                system_prompt="Test agent."
            )
            await AgentService.create_agent(test_session, agent_data)

        # List agents
        agents, total = await AgentService.list_agents(test_session, skip=0, limit=10)

        assert len(agents) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_agents_with_pagination(self, test_session):
        """Test agent list pagination."""
        # Create 10 agents
        for i in range(10):
            agent_data = AgentCreate(
                name=f"Page Agent {i}",
                description=f"Agent {i}",
                agent_type=AgentType.ANALYTICAL,
                model="claude-3-5-sonnet-20241022",
                system_prompt="Test agent."
            )
            await AgentService.create_agent(test_session, agent_data)

        # Get first page
        agents_page1, total = await AgentService.list_agents(
            test_session, skip=0, limit=5
        )
        assert len(agents_page1) == 5
        assert total == 10

        # Get second page
        agents_page2, _ = await AgentService.list_agents(
            test_session, skip=5, limit=5
        )
        assert len(agents_page2) == 5

        # Ensure no overlap
        page1_ids = {a.id for a in agents_page1}
        page2_ids = {a.id for a in agents_page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_list_agents_filter_by_status(self, test_session):
        """Test filtering agents by status."""
        # Create agents with different statuses
        for status in [AgentStatus.ACTIVE, AgentStatus.INACTIVE]:
            agent_data = AgentCreate(
                name=f"Status {status.value} Agent",
                description="Test agent",
                agent_type=AgentType.CREATIVE,
                model="claude-3-5-sonnet-20241022",
                system_prompt="Test agent."
            )
            agent = await AgentService.create_agent(test_session, agent_data)
            # Update status
            await AgentService.update_agent_status(
                test_session,
                agent.id,
                AgentStatusUpdate(status=status)
            )

        # Filter by active
        agents, total = await AgentService.list_agents(
            test_session, status=AgentStatus.ACTIVE
        )
        assert total == 1
        assert all(a.status == AgentStatus.ACTIVE for a in agents)

    @pytest.mark.asyncio
    async def test_list_agents_search(self, test_session):
        """Test searching agents."""
        # Create agents with searchable names
        agent_data1 = AgentCreate(
            name="Customer Support Bot",
            description="Handles customer inquiries",
            agent_type=AgentType.CONVERSATIONAL,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test agent."
        )
        await AgentService.create_agent(test_session, agent_data1)

        agent_data2 = AgentCreate(
            name="Data Analyst",
            description="Analyzes data",
            agent_type=AgentType.ANALYTICAL,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test agent."
        )
        await AgentService.create_agent(test_session, agent_data2)

        # Search for "customer"
        agents, total = await AgentService.list_agents(
            test_session, search="customer"
        )
        assert total == 1
        assert "Customer" in agents[0].name

    @pytest.mark.asyncio
    async def test_update_agent(self, test_session):
        """Test updating an agent."""
        # Create agent
        agent_data = AgentCreate(
            name="Update Agent",
            description="Original description",
            agent_type=AgentType.AUTOMATION,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Original prompt",
            temperature=0.5
        )
        agent = await AgentService.create_agent(test_session, agent_data)

        # Update agent
        update_data = AgentUpdate(
            description="Updated description",
            temperature=0.9
        )
        updated_agent = await AgentService.update_agent(
            test_session, agent.id, update_data
        )

        assert updated_agent is not None
        assert updated_agent.description == "Updated description"
        assert updated_agent.temperature == 0.9
        assert updated_agent.name == "Update Agent"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_agent_not_found(self, test_session):
        """Test updating non-existent agent returns None."""
        update_data = AgentUpdate(description="New description")
        updated_agent = await AgentService.update_agent(
            test_session, str(uuid.uuid4()), update_data
        )
        assert updated_agent is None

    @pytest.mark.asyncio
    async def test_update_agent_status(self, test_session):
        """Test updating agent status."""
        # Create agent
        agent_data = AgentCreate(
            name="Status Update Agent",
            description="Test agent",
            agent_type=AgentType.CONVERSATIONAL,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test agent."
        )
        agent = await AgentService.create_agent(test_session, agent_data)
        assert agent.status == AgentStatus.INACTIVE

        # Update status
        status_update = AgentStatusUpdate(status=AgentStatus.ACTIVE)
        updated_agent = await AgentService.update_agent_status(
            test_session, agent.id, status_update
        )

        assert updated_agent is not None
        assert updated_agent.status == AgentStatus.ACTIVE
        assert updated_agent.last_active is not None

    @pytest.mark.asyncio
    async def test_delete_agent(self, test_session):
        """Test deleting an agent."""
        # Create agent
        agent_data = AgentCreate(
            name="Delete Agent",
            description="Test agent",
            agent_type=AgentType.ANALYTICAL,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test agent."
        )
        agent = await AgentService.create_agent(test_session, agent_data)

        # Delete agent
        deleted = await AgentService.delete_agent(test_session, agent.id)
        assert deleted is True

        # Verify deletion
        agent = await AgentService.get_agent(test_session, agent.id)
        assert agent is None

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, test_session):
        """Test deleting non-existent agent returns False."""
        deleted = await AgentService.delete_agent(test_session, str(uuid.uuid4()))
        assert deleted is False
