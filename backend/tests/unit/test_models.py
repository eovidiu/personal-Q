"""
Unit tests for database models.
"""

import pytest
from datetime import datetime
import uuid
import sys
import os


from app.models.agent import Agent, AgentStatus, AgentType
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.activity import Activity, ActivityType, ActivityStatus
from app.models.api_key import APIKey
from app.models.schedule import Schedule


class TestAgentModel:
    """Tests for Agent model."""

    @pytest.mark.asyncio
    async def test_create_agent(self, test_session):
        """Test creating an agent."""
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CONVERSATIONAL,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            system_prompt="You are a test agent.",
            tags=["test"],
            tasks_completed=0,
            tasks_failed=0,
        )

        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)

        assert agent.id is not None
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.CONVERSATIONAL
        assert agent.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_agent_success_rate(self, test_session):
        """Test agent success rate calculation."""
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.ANALYTICAL,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent.",
            tasks_completed=80,
            tasks_failed=20,
        )

        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)

        assert agent.success_rate == 80.0

    @pytest.mark.asyncio
    async def test_agent_success_rate_zero_tasks(self, test_session):
        """Test success rate with zero tasks."""
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CREATIVE,
            status=AgentStatus.INACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent.",
            tasks_completed=0,
            tasks_failed=0,
        )

        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)

        assert agent.success_rate == 0.0


class TestTaskModel:
    """Tests for Task model."""

    @pytest.mark.asyncio
    async def test_create_task(self, test_session):
        """Test creating a task."""
        # Create agent first
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.AUTOMATION,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent.",
        )
        test_session.add(agent)
        await test_session.commit()

        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            input_data={"key": "value"},
        )

        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)

        assert task.id is not None
        assert task.agent_id == agent.id
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH


class TestActivityModel:
    """Tests for Activity model."""

    @pytest.mark.asyncio
    async def test_create_activity(self, test_session):
        """Test creating an activity."""
        # Create agent first
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CONVERSATIONAL,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent.",
        )
        test_session.add(agent)
        await test_session.commit()

        # Create activity
        activity = Activity(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            activity_type=ActivityType.AGENT_STARTED,
            status=ActivityStatus.SUCCESS,
            title="Agent Started",
            description="Test agent started successfully",
            activity_metadata={"test": "data"},
        )

        test_session.add(activity)
        await test_session.commit()
        await test_session.refresh(activity)

        assert activity.id is not None
        assert activity.agent_id == agent.id
        assert activity.activity_type == ActivityType.AGENT_STARTED
        assert activity.status == ActivityStatus.SUCCESS


class TestAPIKeyModel:
    """Tests for APIKey model."""

    @pytest.mark.asyncio
    async def test_create_api_key(self, test_session):
        """Test creating an API key."""
        api_key = APIKey(
            id=str(uuid.uuid4()),
            service_name="anthropic",
            api_key="sk-test-key-12345",
            is_active=True,
        )

        test_session.add(api_key)
        await test_session.commit()
        await test_session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.service_name == "anthropic"
        assert api_key.api_key == "sk-test-key-12345"
        assert api_key.is_active is True


class TestScheduleModel:
    """Tests for Schedule model."""

    @pytest.mark.asyncio
    async def test_create_schedule(self, test_session):
        """Test creating a schedule."""
        # Create agent first
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.AUTOMATION,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent.",
        )
        test_session.add(agent)
        await test_session.commit()

        # Create schedule
        schedule = Schedule(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            name="Daily Report",
            description="Generate daily report",
            cron_expression="0 9 * * *",
            task_config={"report_type": "daily"},
            is_active=True,
        )

        test_session.add(schedule)
        await test_session.commit()
        await test_session.refresh(schedule)

        assert schedule.id is not None
        assert schedule.agent_id == agent.id
        assert schedule.name == "Daily Report"
        assert schedule.cron_expression == "0 9 * * *"
        assert schedule.is_active is True
