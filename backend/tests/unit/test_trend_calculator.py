"""Unit tests for TrendCalculator service."""

from datetime import timedelta

import pytest
from app.models.agent import Agent, AgentStatus, AgentType
from app.models.task import Task, TaskPriority, TaskStatus
from app.services.trend_calculator import TrendCalculator
from app.utils.datetime_utils import utcnow
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_calculate_agent_trend_no_agents(test_session: AsyncSession):
    """Test agent trend calculation with no agents."""
    trend = await TrendCalculator.calculate_agent_trend(test_session)
    assert trend == "No change this week"


@pytest.mark.asyncio
async def test_calculate_agent_trend_new_agents(test_session: AsyncSession):
    """Test agent trend with new agents created this week."""
    now = utcnow()

    # Create 3 agents in the last 7 days
    for i in range(3):
        agent = Agent(
            id=f"agent-{i}",
            name=f"Test Agent {i}",
            description="Test agent",
            agent_type=AgentType.CONVERSATIONAL,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test prompt",
            created_at=now - timedelta(days=i),
            updated_at=now,
        )
        test_session.add(agent)

    await test_session.commit()

    trend = await TrendCalculator.calculate_agent_trend(test_session)
    assert trend == "+3 this week"


@pytest.mark.asyncio
async def test_calculate_tasks_trend_no_data(test_session: AsyncSession):
    """Test tasks trend with no historical data."""
    trend = await TrendCalculator.calculate_tasks_trend(test_session)
    assert trend == "No data"


@pytest.mark.asyncio
async def test_calculate_tasks_trend_with_growth(test_session: AsyncSession):
    """Test tasks trend showing growth."""
    now = utcnow()

    # Create a test agent
    agent = Agent(
        id="agent-1",
        name="Test Agent",
        description="Test agent",
        agent_type=AgentType.CONVERSATIONAL,
        status=AgentStatus.ACTIVE,
        model="claude-3-5-sonnet-20241022",
        system_prompt="Test prompt",
        created_at=now - timedelta(days=60),
        updated_at=now,
    )
    test_session.add(agent)

    # Create 10 tasks completed in last 30 days
    for i in range(10):
        task = Task(
            id=f"task-recent-{i}",
            agent_id="agent-1",
            title=f"Recent Task {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=i + 1),
            completed_at=now - timedelta(days=i + 1),
            updated_at=now,
        )
        test_session.add(task)

    # Create 5 tasks completed 30-60 days ago
    for i in range(5):
        task = Task(
            id=f"task-old-{i}",
            agent_id="agent-1",
            title=f"Old Task {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=31 + i),
            completed_at=now - timedelta(days=31 + i),
            updated_at=now,
        )
        test_session.add(task)

    await test_session.commit()

    trend = await TrendCalculator.calculate_tasks_trend(test_session)
    # Growth: (10 - 5) / 5 * 100 = 100%
    assert trend == "+100.0% from last month"


@pytest.mark.asyncio
async def test_calculate_tasks_trend_with_decline(test_session: AsyncSession):
    """Test tasks trend showing decline."""
    now = utcnow()

    # Create a test agent
    agent = Agent(
        id="agent-1",
        name="Test Agent",
        description="Test agent",
        agent_type=AgentType.CONVERSATIONAL,
        status=AgentStatus.ACTIVE,
        model="claude-3-5-sonnet-20241022",
        system_prompt="Test prompt",
        created_at=now - timedelta(days=60),
        updated_at=now,
    )
    test_session.add(agent)

    # Create 5 tasks completed in last 30 days
    for i in range(5):
        task = Task(
            id=f"task-recent-{i}",
            agent_id="agent-1",
            title=f"Recent Task {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=i + 1),
            completed_at=now - timedelta(days=i + 1),
            updated_at=now,
        )
        test_session.add(task)

    # Create 10 tasks completed 30-60 days ago
    for i in range(10):
        task = Task(
            id=f"task-old-{i}",
            agent_id="agent-1",
            title=f"Old Task {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=31 + i),
            completed_at=now - timedelta(days=31 + i),
            updated_at=now,
        )
        test_session.add(task)

    await test_session.commit()

    trend = await TrendCalculator.calculate_tasks_trend(test_session)
    # Decline: (5 - 10) / 10 * 100 = -50%
    assert trend == "-50.0% from last month"


@pytest.mark.asyncio
async def test_calculate_tasks_trend_new_baseline(test_session: AsyncSession):
    """Test tasks trend with no previous period data."""
    now = utcnow()

    # Create a test agent
    agent = Agent(
        id="agent-1",
        name="Test Agent",
        description="Test agent",
        agent_type=AgentType.CONVERSATIONAL,
        status=AgentStatus.ACTIVE,
        model="claude-3-5-sonnet-20241022",
        system_prompt="Test prompt",
        created_at=now - timedelta(days=15),
        updated_at=now,
    )
    test_session.add(agent)

    # Create 5 tasks completed in last 30 days only
    for i in range(5):
        task = Task(
            id=f"task-{i}",
            agent_id="agent-1",
            title=f"Task {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=i + 1),
            completed_at=now - timedelta(days=i + 1),
            updated_at=now,
        )
        test_session.add(task)

    await test_session.commit()

    trend = await TrendCalculator.calculate_tasks_trend(test_session)
    assert trend == "+5 from last month (new baseline)"


@pytest.mark.asyncio
async def test_calculate_success_rate_trend_no_data(test_session: AsyncSession):
    """Test success rate trend with no data."""
    trend = await TrendCalculator.calculate_success_rate_trend(test_session)
    assert trend == "No data"


@pytest.mark.asyncio
async def test_calculate_success_rate_trend_improving(test_session: AsyncSession):
    """Test success rate trend showing improvement."""
    now = utcnow()

    # Create a test agent
    agent = Agent(
        id="agent-1",
        name="Test Agent",
        description="Test agent",
        agent_type=AgentType.CONVERSATIONAL,
        status=AgentStatus.ACTIVE,
        model="claude-3-5-sonnet-20241022",
        system_prompt="Test prompt",
        created_at=now - timedelta(days=60),
        updated_at=now,
    )
    test_session.add(agent)

    # Last 30 days: 9 completed, 1 failed = 90% success rate
    for i in range(9):
        task = Task(
            id=f"task-recent-success-{i}",
            agent_id="agent-1",
            title=f"Recent Success {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=i + 1),
            completed_at=now - timedelta(days=i + 1),
            updated_at=now,
        )
        test_session.add(task)

    task = Task(
        id="task-recent-failed",
        agent_id="agent-1",
        title="Recent Failed",
        status=TaskStatus.FAILED,
        priority=TaskPriority.MEDIUM,
        created_at=now - timedelta(days=10),
        completed_at=now - timedelta(days=10),
        updated_at=now,
    )
    test_session.add(task)

    # Previous 30 days (30-60 days ago): 6 completed, 4 failed = 60% success rate
    for i in range(6):
        task = Task(
            id=f"task-old-success-{i}",
            agent_id="agent-1",
            title=f"Old Success {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=31 + i),
            completed_at=now - timedelta(days=31 + i),
            updated_at=now,
        )
        test_session.add(task)

    for i in range(4):
        task = Task(
            id=f"task-old-failed-{i}",
            agent_id="agent-1",
            title=f"Old Failed {i}",
            status=TaskStatus.FAILED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=31 + i),
            completed_at=now - timedelta(days=31 + i),
            updated_at=now,
        )
        test_session.add(task)

    await test_session.commit()

    trend = await TrendCalculator.calculate_success_rate_trend(test_session)
    # Improvement: 90% - 60% = +30%
    assert trend == "+30.0% from last month"


@pytest.mark.asyncio
async def test_calculate_success_rate_trend_declining(test_session: AsyncSession):
    """Test success rate trend showing decline."""
    now = utcnow()

    # Create a test agent
    agent = Agent(
        id="agent-1",
        name="Test Agent",
        description="Test agent",
        agent_type=AgentType.CONVERSATIONAL,
        status=AgentStatus.ACTIVE,
        model="claude-3-5-sonnet-20241022",
        system_prompt="Test prompt",
        created_at=now - timedelta(days=60),
        updated_at=now,
    )
    test_session.add(agent)

    # Last 30 days: 6 completed, 4 failed = 60% success rate
    for i in range(6):
        task = Task(
            id=f"task-recent-success-{i}",
            agent_id="agent-1",
            title=f"Recent Success {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=i + 1),
            completed_at=now - timedelta(days=i + 1),
            updated_at=now,
        )
        test_session.add(task)

    for i in range(4):
        task = Task(
            id=f"task-recent-failed-{i}",
            agent_id="agent-1",
            title=f"Recent Failed {i}",
            status=TaskStatus.FAILED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=i + 1),
            completed_at=now - timedelta(days=i + 1),
            updated_at=now,
        )
        test_session.add(task)

    # Previous 30 days (30-60 days ago): 9 completed, 1 failed = 90% success rate
    for i in range(9):
        task = Task(
            id=f"task-old-success-{i}",
            agent_id="agent-1",
            title=f"Old Success {i}",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=now - timedelta(days=31 + i),
            completed_at=now - timedelta(days=31 + i),
            updated_at=now,
        )
        test_session.add(task)

    task = Task(
        id="task-old-failed",
        agent_id="agent-1",
        title="Old Failed",
        status=TaskStatus.FAILED,
        priority=TaskPriority.MEDIUM,
        created_at=now - timedelta(days=31),
        completed_at=now - timedelta(days=31),
        updated_at=now,
    )
    test_session.add(task)

    await test_session.commit()

    trend = await TrendCalculator.calculate_success_rate_trend(test_session)
    # Decline: 60% - 90% = -30%
    assert trend == "-30.0% from last month"
