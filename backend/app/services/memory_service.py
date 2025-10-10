"""
ABOUTME: Memory service using ChromaDB with proper async/await support.
ABOUTME: All ChromaDB operations run in executor to avoid blocking event loop.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

from app.db.chroma_client import get_chroma_client
from app.utils.datetime_utils import utcnow
from config.settings import settings

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for agent memory and context management with async support."""

    def __init__(self):
        self.chroma = get_chroma_client()
        self.conversations_collection = self.chroma.get_or_create_collection("conversations")
        self.outputs_collection = self.chroma.get_or_create_collection("agent_outputs")
        self.documents_collection = self.chroma.get_or_create_collection("documents")

    async def store_conversation(
        self,
        agent_id: str,
        message: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
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

        # Run ChromaDB operation in executor
        await asyncio.to_thread(
            self.conversations_collection.add,
            documents=[message],
            metadatas=[{
                "agent_id": agent_id,
                "role": role,
                "timestamp": timestamp,
                **(metadata or {})
            }],
            ids=[memory_id]
        )

        return memory_id

    async def store_agent_output(
        self,
        agent_id: str,
        task_id: str,
        output: str,
        metadata: Dict[str, Any] = None
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

        # Run ChromaDB operation in executor
        await asyncio.to_thread(
            self.outputs_collection.add,
            documents=[output],
            metadatas=[{
                "agent_id": agent_id,
                "task_id": task_id,
                "timestamp": timestamp,
                **(metadata or {})
            }],
            ids=[memory_id]
        )

        return memory_id

    async def store_document(
        self,
        content: str,
        source: str,
        metadata: Dict[str, Any] = None
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

        # Run ChromaDB operation in executor
        await asyncio.to_thread(
            self.documents_collection.add,
            documents=[content],
            metadatas=[{
                "source": source,
                "timestamp": timestamp,
                **(metadata or {})
            }],
            ids=[doc_id]
        )

        return doc_id

    async def search_conversations(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 5
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
        where_filter = {"agent_id": agent_id} if agent_id else None

        # Run ChromaDB query in executor
        results = await asyncio.to_thread(
            self.conversations_collection.query,
            query_texts=[query],
            n_results=limit,
            where=where_filter
        )

        # Format results
        conversations = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                conversations.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        return conversations

    async def search_agent_outputs(
        self,
        query: str,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 5
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
        where_filter = {}
        if agent_id:
            where_filter["agent_id"] = agent_id
        if task_id:
            where_filter["task_id"] = task_id

        # Run ChromaDB query in executor
        results = await asyncio.to_thread(
            self.outputs_collection.query,
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None
        )

        # Format results
        outputs = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                outputs.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        return outputs

    async def search_documents(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents for RAG (async).

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching documents
        """
        # Run ChromaDB query in executor
        results = await asyncio.to_thread(
            self.documents_collection.query,
            query_texts=[query],
            n_results=limit
        )

        # Format results
        documents = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        return documents

    async def get_conversation_history(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for agent (async).

        Args:
            agent_id: Agent ID
            limit: Maximum messages to retrieve

        Returns:
            List of recent conversations
        """
        # Run ChromaDB query in executor
        results = await asyncio.to_thread(
            self.conversations_collection.get,
            where={"agent_id": agent_id},
            limit=limit
        )

        # Format results
        conversations = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                conversations.append({
                    "id": results["ids"][i],
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })

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

        # Clean conversations
        def _cleanup_collection(collection):
            count = 0
            results = collection.get(where={"timestamp": {"$lt": cutoff_str}})
            if results["ids"]:
                collection.delete(ids=results["ids"])
                count = len(results["ids"])
            return count

        # Run cleanup in executor
        deleted_count += await asyncio.to_thread(_cleanup_collection, self.conversations_collection)
        deleted_count += await asyncio.to_thread(_cleanup_collection, self.outputs_collection)

        logger.info(f"Cleaned up {deleted_count} old memory entries (older than {days} days)")
        return deleted_count

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics (async).

        Returns:
            Statistics about stored memories
        """
        def _get_counts():
            conv_count = self.conversations_collection.count()
            output_count = self.outputs_collection.count()
            doc_count = self.documents_collection.count()
            return conv_count, output_count, doc_count

        # Run in executor
        conv_count, output_count, doc_count = await asyncio.to_thread(_get_counts)

        return {
            "conversations": conv_count,
            "agent_outputs": output_count,
            "documents": doc_count,
            "total": conv_count + output_count + doc_count
        }


# Global service instance
memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    return memory_service
