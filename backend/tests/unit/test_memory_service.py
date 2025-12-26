"""
Unit tests for Memory service.
"""

import pytest
from unittest.mock import Mock, patch


from app.services.memory_service import MemoryService


class TestMemoryService:
    """Tests for Memory Service."""

    @pytest.fixture
    def mock_tables(self):
        """Create mock tables with LanceDB-like methods."""
        conv_table = Mock()
        conv_table.__len__ = Mock(return_value=0)
        conv_table.add = Mock()
        conv_table.search = Mock(return_value=Mock(
            limit=Mock(return_value=Mock(
                where=Mock(return_value=Mock(to_list=Mock(return_value=[]))),
                to_list=Mock(return_value=[])
            ))
        ))

        outputs_table = Mock()
        outputs_table.__len__ = Mock(return_value=0)
        outputs_table.add = Mock()
        outputs_table.search = Mock(return_value=Mock(
            limit=Mock(return_value=Mock(
                where=Mock(return_value=Mock(to_list=Mock(return_value=[]))),
                to_list=Mock(return_value=[])
            ))
        ))

        docs_table = Mock()
        docs_table.__len__ = Mock(return_value=0)
        docs_table.add = Mock()
        docs_table.search = Mock(return_value=Mock(
            limit=Mock(return_value=Mock(to_list=Mock(return_value=[])))
        ))

        return {
            "conversations": conv_table,
            "agent_outputs": outputs_table,
            "documents": docs_table
        }

    @pytest.fixture
    def mock_lance_client(self, mock_tables):
        """Create mock LanceDB client."""
        client = Mock()

        def get_or_create_table(name, schema=None, **kwargs):
            return mock_tables.get(name, Mock())

        client.get_or_create_table = Mock(side_effect=get_or_create_table)
        return client

    @pytest.fixture
    def memory_service(self, mock_lance_client):
        """Create memory service with mocked client."""
        with patch("app.services.memory_service.get_lance_client", return_value=mock_lance_client):
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
        # Mock table lengths using len()
        memory_service.conversations_table.__len__ = Mock(return_value=100)
        memory_service.outputs_table.__len__ = Mock(return_value=50)
        memory_service.documents_table.__len__ = Mock(return_value=25)

        stats = await memory_service.get_statistics()

        assert stats["conversations"] == 100
        assert stats["agent_outputs"] == 50
        assert stats["documents"] == 25
        assert stats["total"] == 175
