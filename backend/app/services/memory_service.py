"""
ABOUTME: Memory service using LanceDB with proper async/await support.
ABOUTME: All LanceDB operations run in executor to avoid blocking event loop.
ABOUTME: Uses sentence-transformers for local embeddings (no API calls needed).
"""

import asyncio
import json
import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.db.lance_client import (
    AgentOutputSchema,
    ConversationSchema,
    DocumentSchema,
    get_lance_client,
)
from app.utils.datetime_utils import utcnow
from config.settings import settings

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for agent memory and context management with async support."""

    def __init__(self):
        self.lance = get_lance_client()
        self.conversations_table = self.lance.get_or_create_table(
            "conversations", ConversationSchema
        )
        self.outputs_table = self.lance.get_or_create_table(
            "agent_outputs", AgentOutputSchema
        )
        self.documents_table = self.lance.get_or_create_table(
            "documents", DocumentSchema
        )

    async def store_conversation(
        self, agent_id: str, message: str, role: str = "user", metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store conversation message in memory (async).

        Args:
            agent_id: Agent ID
            message: Conversation message
            role: Message role (user/assistant)
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        timestamp = utcnow().isoformat()

        data = {
            "id": memory_id,
            "text": message,
            "agent_id": agent_id,
            "role": role,
            "timestamp": timestamp,
            "metadata_json": json.dumps(metadata) if metadata else None,
        }

        # Run LanceDB operation in executor
        await asyncio.to_thread(self.conversations_table.add, [data])

        return memory_id

    async def store_agent_output(
        self, agent_id: str, task_id: str, output: str, metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store agent output in memory (async).

        Args:
            agent_id: Agent ID
            task_id: Task ID
            output: Agent output text
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        timestamp = utcnow().isoformat()

        data = {
            "id": memory_id,
            "text": output,
            "agent_id": agent_id,
            "task_id": task_id,
            "timestamp": timestamp,
            "metadata_json": json.dumps(metadata) if metadata else None,
        }

        # Run LanceDB operation in executor
        await asyncio.to_thread(self.outputs_table.add, [data])

        return memory_id

    async def store_document(
        self, content: str, source: str, metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store document for RAG (async).

        Args:
            content: Document content
            source: Document source
            metadata: Additional metadata

        Returns:
            Document ID
        """
        doc_id = str(uuid.uuid4())
        timestamp = utcnow().isoformat()

        data = {
            "id": doc_id,
            "text": content,
            "source": source,
            "timestamp": timestamp,
            "metadata_json": json.dumps(metadata) if metadata else None,
        }

        # Run LanceDB operation in executor
        await asyncio.to_thread(self.documents_table.add, [data])

        return doc_id

    async def search_conversations(
        self, query: str, agent_id: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search conversation history (async).

        Args:
            query: Search query
            agent_id: Filter by agent ID
            limit: Maximum results

        Returns:
            List of matching conversations
        """

        def _search():
            search_query = self.conversations_table.search(query).limit(limit)
            if agent_id:
                search_query = search_query.where(f"agent_id = '{agent_id}'")
            return search_query.to_list()

        # Run LanceDB query in executor
        results = await asyncio.to_thread(_search)

        # Format results
        conversations = []
        for row in results:
            metadata = {"agent_id": row["agent_id"], "role": row["role"], "timestamp": row["timestamp"]}
            if row.get("metadata_json"):
                metadata.update(json.loads(row["metadata_json"]))
            conversations.append(
                {
                    "content": row["text"],
                    "metadata": metadata,
                    "distance": row.get("_distance"),
                }
            )

        return conversations

    async def search_agent_outputs(
        self,
        query: str,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search agent outputs (async).

        Args:
            query: Search query
            agent_id: Filter by agent ID
            task_id: Filter by task ID
            limit: Maximum results

        Returns:
            List of matching outputs
        """

        def _search():
            search_query = self.outputs_table.search(query).limit(limit)

            # Build filter conditions
            conditions = []
            if agent_id:
                conditions.append(f"agent_id = '{agent_id}'")
            if task_id:
                conditions.append(f"task_id = '{task_id}'")

            if conditions:
                where_clause = " AND ".join(conditions)
                search_query = search_query.where(where_clause)

            return search_query.to_list()

        # Run LanceDB query in executor
        results = await asyncio.to_thread(_search)

        # Format results
        outputs = []
        for row in results:
            metadata = {
                "agent_id": row["agent_id"],
                "task_id": row["task_id"],
                "timestamp": row["timestamp"],
            }
            if row.get("metadata_json"):
                metadata.update(json.loads(row["metadata_json"]))
            outputs.append(
                {
                    "content": row["text"],
                    "metadata": metadata,
                    "distance": row.get("_distance"),
                }
            )

        return outputs

    async def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents for RAG (async).

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching documents
        """

        def _search():
            return self.documents_table.search(query).limit(limit).to_list()

        # Run LanceDB query in executor
        results = await asyncio.to_thread(_search)

        # Format results
        documents = []
        for row in results:
            metadata = {"source": row["source"], "timestamp": row["timestamp"]}
            if row.get("metadata_json"):
                metadata.update(json.loads(row["metadata_json"]))
            documents.append(
                {
                    "content": row["text"],
                    "metadata": metadata,
                    "distance": row.get("_distance"),
                }
            )

        return documents

    async def get_conversation_history(
        self, agent_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for agent (async).

        Args:
            agent_id: Agent ID
            limit: Maximum messages to retrieve

        Returns:
            List of recent conversations
        """

        def _get_history():
            # Use search without vector query to get filtered results
            return (
                self.conversations_table.search()
                .where(f"agent_id = '{agent_id}'")
                .limit(limit)
                .to_list()
            )

        # Run LanceDB query in executor
        results = await asyncio.to_thread(_get_history)

        # Format results
        conversations = []
        for row in results:
            metadata = {"agent_id": row["agent_id"], "role": row["role"], "timestamp": row["timestamp"]}
            if row.get("metadata_json"):
                metadata.update(json.loads(row["metadata_json"]))
            conversations.append(
                {
                    "id": row["id"],
                    "content": row["text"],
                    "metadata": metadata,
                }
            )

        return conversations

    async def cleanup_old_memories(self, days: int = None) -> int:
        """
        Clean up old memory entries (async).

        Args:
            days: Number of days to keep (default from settings)

        Returns:
            Number of entries deleted
        """
        days = days or settings.memory_retention_days
        cutoff_date = utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()

        deleted_count = 0

        def _cleanup_table(table):
            # Count rows before deletion
            try:
                before_count = len(table)
            except Exception:
                before_count = 0

            # Delete old entries using SQL-like filter
            try:
                table.delete(f"timestamp < '{cutoff_str}'")
            except Exception as e:
                logger.debug(f"Cleanup skipped: {e}")
                return 0

            # Count rows after deletion
            try:
                after_count = len(table)
            except Exception:
                after_count = 0

            return max(0, before_count - after_count)

        # Run cleanup in executor
        deleted_count += await asyncio.to_thread(_cleanup_table, self.conversations_table)
        deleted_count += await asyncio.to_thread(_cleanup_table, self.outputs_table)

        logger.info(f"Cleaned up {deleted_count} old memory entries (older than {days} days)")
        return deleted_count

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics (async).

        Returns:
            Statistics about stored memories
        """

        def _get_counts():
            try:
                conv_count = len(self.conversations_table)
            except Exception:
                conv_count = 0
            try:
                output_count = len(self.outputs_table)
            except Exception:
                output_count = 0
            try:
                doc_count = len(self.documents_table)
            except Exception:
                doc_count = 0
            return conv_count, output_count, doc_count

        # Run in executor
        conv_count, output_count, doc_count = await asyncio.to_thread(_get_counts)

        return {
            "conversations": conv_count,
            "agent_outputs": output_count,
            "documents": doc_count,
            "total": conv_count + output_count + doc_count,
        }


# Global service instance
memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    return memory_service
