"""
Unit tests for database connections and utilities.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.database import get_db, init_db, close_db
from app.db.chroma_client import ChromaDBClient, get_chroma_client


class TestDatabaseConnection:
    """Tests for SQLite database connection."""

    @pytest.mark.asyncio
    async def test_get_db_session(self, test_engine):
        """Test getting database session."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        async_session_maker = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session_maker() as session:
            assert session is not None
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio
    async def test_init_db(self, test_engine):
        """Test database initialization."""
        from app.db.database import Base

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verify tables exist
        async with test_engine.connect() as conn:
            from sqlalchemy import inspect
            inspector = await conn.run_sync(inspect)
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

            assert "agents" in tables
            assert "tasks" in tables
            assert "activities" in tables
            assert "api_keys" in tables
            assert "schedules" in tables


class TestChromaDBClient:
    """Tests for ChromaDB client."""

    def test_chromadb_singleton(self):
        """Test ChromaDB client is singleton."""
        client1 = ChromaDBClient()
        client2 = ChromaDBClient()

        assert client1 is client2

    def test_get_chroma_client(self):
        """Test get_chroma_client dependency."""
        client = get_chroma_client()

        assert client is not None
        assert isinstance(client, ChromaDBClient)

    def test_create_collection(self):
        """Test creating a ChromaDB collection."""
        client = get_chroma_client()

        collection = client.get_or_create_collection(
            name="test_collection",
            metadata={"test": "metadata"}
        )

        assert collection is not None
        assert collection.name == "test_collection"

        # Cleanup
        client.delete_collection("test_collection")

    def test_list_collections(self):
        """Test listing ChromaDB collections."""
        client = get_chroma_client()

        # Create test collection
        client.get_or_create_collection(name="test_list")

        collections = client.list_collections()
        collection_names = [c.name for c in collections]

        assert "test_list" in collection_names

        # Cleanup
        client.delete_collection("test_list")
