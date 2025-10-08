"""
Unit tests for Memory service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.memory_service import MemoryService


class TestMemoryService:
    """Tests for Memory Service."""

    @pytest.fixture
    def mock_chroma_client(self):
        """Create mock ChromaDB client."""
        client = Mock()
        client.get_or_create_collection = Mock(return_value=Mock())
        return client

    @pytest.fixture
    def memory_service(self, mock_chroma_client):
        """Create memory service with mocked client."""
        with patch("app.services.memory_service.get_chroma_client", return_value=mock_chroma_client):
            service = MemoryService()
            return service

    @pytest.mark.asyncio
    async def test_store_conversation(self, memory_service):
        """Test storing conversation."""
        memory_id = await memory_service.store_conversation(
            agent_id="test-agent",
            message="Hello, world!",
            role="user"
        )
        assert memory_id is not None
        assert isinstance(memory_id, str)

    @pytest.mark.asyncio
    async def test_store_agent_output(self, memory_service):
        """Test storing agent output."""
        memory_id = await memory_service.store_agent_output(
            agent_id="test-agent",
            task_id="test-task",
            output="Task completed successfully"
        )
        assert memory_id is not None
        assert isinstance(memory_id, str)

    @pytest.mark.asyncio
    async def test_store_document(self, memory_service):
        """Test storing document."""
        doc_id = await memory_service.store_document(
            content="Document content here",
            source="test-source"
        )
        assert doc_id is not None
        assert isinstance(doc_id, str)

    @pytest.mark.asyncio
    async def test_get_statistics(self, memory_service):
        """Test getting memory statistics."""
        # Mock collection counts
        memory_service.conversations_collection.count = Mock(return_value=100)
        memory_service.outputs_collection.count = Mock(return_value=50)
        memory_service.documents_collection.count = Mock(return_value=25)

        stats = await memory_service.get_statistics()

        assert stats["conversations_count"] == 100
        assert stats["outputs_count"] == 50
        assert stats["documents_count"] == 25
        assert "retention_days" in stats
