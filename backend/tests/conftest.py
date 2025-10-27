"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
from unittest.mock import AsyncMock, Mock, patch

# Mock the rate limiter BEFORE any app imports to avoid Redis connection attempts
mock_limiter = Mock()
mock_limiter.limit = lambda *args, **kwargs: lambda func: func  # Bypass decorator

# Apply the patch at module level
limiter_patcher = patch('app.middleware.rate_limit.limiter', mock_limiter)
limiter_patcher.start()

from fastapi import FastAPI
from app.db.database import Base, get_db
from app.models import Agent, Task, Activity, APIKey, Schedule


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_session):
    """Override get_db dependency."""

    async def _override_get_db():
        yield test_session

    return _override_get_db


@pytest.fixture
async def test_app(test_engine, test_session):
    """Create test FastAPI app with overridden dependencies."""
    from config.settings import settings

    # Create app with empty lifespan to skip DB/Redis initialization
    @asynccontextmanager
    async def empty_lifespan(app: FastAPI):
        # Initialize database tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=empty_lifespan,
    )

    # Import and include routers
    from app.routers import activities, agents, auth, metrics, tasks, websocket
    from app.routers import settings as settings_router

    app.include_router(agents.router, prefix=f"{settings.api_prefix}/agents", tags=["agents"])
    app.include_router(tasks.router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"])
    app.include_router(
        activities.router, prefix=f"{settings.api_prefix}/activities", tags=["activities"]
    )
    app.include_router(
        settings_router.router, prefix=f"{settings.api_prefix}/settings", tags=["settings"]
    )
    app.include_router(metrics.router, prefix=f"{settings.api_prefix}/metrics", tags=["metrics"])

    # Override database dependency
    async def _override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = _override_get_db

    # Override authentication dependency for tests
    # The override should be a simple function without dependency parameters
    from app.dependencies.auth import get_current_user

    async def _mock_current_user():
        return {"sub": "test-user-id", "email": "test@example.com"}

    app.dependency_overrides[get_current_user] = _mock_current_user

    # Set the already-mocked limiter to app.state for consistency
    app.state.limiter = mock_limiter

    return app


@pytest.fixture
async def client(test_app):
    """Create AsyncClient for integration tests."""
    from httpx import AsyncClient

    async with AsyncClient(app=test_app, base_url="http://test", follow_redirects=True) as ac:
        yield ac


@pytest.fixture
def db_session(test_session):
    """Alias for test_session to match test expectations."""
    return test_session


@pytest.fixture
def auth_headers():
    """Provide auth headers for tests (authentication is mocked in test_app)."""
    return {"Authorization": "Bearer mock-token"}


@pytest.fixture
async def sample_agent(test_session):
    """Create a sample agent for testing."""
    from app.models.agent import AgentType, AgentStatus

    agent = Agent(
        id="test-agent-123",
        name="Test Agent",
        description="A test agent for integration tests",
        agent_type=AgentType.CONVERSATIONAL,
        model="claude-3-5-sonnet-20241022",
        system_prompt="You are a helpful test agent.",
        status=AgentStatus.ACTIVE,
        temperature=0.7,
        max_tokens=1000,
    )
    test_session.add(agent)
    await test_session.commit()
    await test_session.refresh(agent)

    yield agent

    # Cleanup
    await test_session.delete(agent)
    await test_session.commit()
