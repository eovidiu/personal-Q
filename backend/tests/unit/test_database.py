"""
Unit tests for database connections and utilities.
"""

import pytest
from unittest.mock import patch, Mock


from app.db.database import get_db, init_db, close_db


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


class TestLanceDBClient:
    """Tests for LanceDB client."""

    def test_lancedb_singleton(self):
        """Test LanceDB client is singleton."""
        # Mock lancedb.connect to avoid actual file system operations
        with patch("app.db.lance_client.lancedb") as mock_lancedb:
            mock_lancedb.connect.return_value = Mock()

            # Import after patching to get mocked version
            from app.db.lance_client import LanceDBClient

            # Reset singleton for test
            LanceDBClient._instance = None
            LanceDBClient._db = None

            client1 = LanceDBClient()
            client2 = LanceDBClient()

            assert client1 is client2

    def test_get_lance_client(self):
        """Test get_lance_client dependency."""
        with patch("app.db.lance_client.lancedb") as mock_lancedb:
            mock_lancedb.connect.return_value = Mock()

            from app.db.lance_client import LanceDBClient, get_lance_client

            # Reset singleton for test
            LanceDBClient._instance = None
            LanceDBClient._db = None

            client = get_lance_client()

            assert client is not None
            assert isinstance(client, LanceDBClient)

    def test_create_table(self):
        """Test creating a LanceDB table."""
        with patch("app.db.lance_client.lancedb") as mock_lancedb:
            mock_db = Mock()
            mock_table = Mock()
            mock_db.create_table.return_value = mock_table
            mock_db.open_table.side_effect = Exception("Table not found")
            mock_lancedb.connect.return_value = mock_db

            from app.db.lance_client import LanceDBClient, ConversationSchema

            # Reset singleton for test
            LanceDBClient._instance = None
            LanceDBClient._db = None

            client = LanceDBClient()
            table = client.get_or_create_table(
                name="test_table",
                schema=ConversationSchema
            )

            assert table is not None
            mock_db.create_table.assert_called_once()

    def test_list_tables(self):
        """Test listing LanceDB tables."""
        with patch("app.db.lance_client.lancedb") as mock_lancedb:
            mock_db = Mock()
            mock_db.table_names.return_value = ["conversations", "documents"]
            mock_lancedb.connect.return_value = mock_db

            from app.db.lance_client import LanceDBClient

            # Reset singleton for test
            LanceDBClient._instance = None
            LanceDBClient._db = None

            client = LanceDBClient()
            tables = client.list_tables()

            assert "conversations" in tables
            assert "documents" in tables
