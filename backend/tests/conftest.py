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
from unittest.mock import AsyncMock

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
def test_app(test_engine, override_get_db):
    """Create test FastAPI app with overridden dependencies."""
    from config.settings import settings

    # Create app with empty lifespan to skip DB/Redis initialization
    @asynccontextmanager
    async def empty_lifespan(app: FastAPI):
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
    app.dependency_overrides[get_db] = override_get_db

    return app
