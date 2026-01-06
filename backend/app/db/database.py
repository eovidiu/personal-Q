"""
Database configuration and session management.
"""

import os

from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

# Determine database type and configure accordingly
_db_url = settings.database_url

if _db_url.startswith("sqlite"):
    # SQLite: use aiosqlite async driver
    DATABASE_URL = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    # Create data directory if it doesn't exist
    db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if db_path and os.path.dirname(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # SQLite-specific engine settings
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug,
    )
elif _db_url.startswith("postgresql"):
    # PostgreSQL: use asyncpg async driver
    DATABASE_URL = _db_url.replace("postgresql://", "postgresql+asyncpg://")

    # PostgreSQL engine settings
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
    )
else:
    raise ValueError(f"Unsupported database URL scheme: {_db_url}")

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()
