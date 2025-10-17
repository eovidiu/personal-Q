"""
Unit tests for Memory service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os


from app.services.memory_service import MemoryService


class TestMemoryService:
    """Tests for Memory Service."""

    @pytest.fixture
    def mock_collections(self):
        """Create mock collections with count methods."""
        conv_collection = Mock()
        conv_collection.count = Mock(return_value=0)
        conv_collection.add = Mock()
        conv_collection.query = Mock(return_value={"documents": [], "metadatas": []})

        outputs_collection = Mock()
        outputs_collection.count = Mock(return_value=0)
        outputs_collection.add = Mock()
        outputs_collection.query = Mock(return_value={"documents": [], "metadatas": []})

        docs_collection = Mock()
        docs_collection.count = Mock(return_value=0)
        docs_collection.add = Mock()
        docs_collection.query = Mock(return_value={"documents": [], "metadatas": []})

        return {
            "conversations": conv_collection,
            "agent_outputs": outputs_collection,
            "documents": docs_collection
        }

    @pytest.fixture
    def mock_chroma_client(self, mock_collections):
        """Create mock ChromaDB client."""
        client = Mock()

        def get_or_create_collection(name, **kwargs):
            return mock_collections.get(name, Mock())

        client.get_or_create_collection = Mock(side_effect=get_or_create_collection)
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

        assert stats["conversations"] == 100
        assert stats["agent_outputs"] == 50
        assert stats["documents"] == 25
        assert "total" in stats or stats["conversations"] + stats["agent_outputs"] + stats["documents"] == 175
