"""
Memory service using ChromaDB for context management.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

from app.db.chroma_client import get_chroma_client
from config.settings import settings


class MemoryService:
    """Service for agent memory and context management."""

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
        Store conversation message in memory.

        Args:
            agent_id: Agent ID
            message: Conversation message
            role: Message role (user/assistant)
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        self.conversations_collection.add(
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
        Store agent output in memory.

        Args:
            agent_id: Agent ID
            task_id: Task ID
            output: Agent output text
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        self.outputs_collection.add(
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
        Store document for RAG.

        Args:
            content: Document content
            source: Document source
            metadata: Additional metadata

        Returns:
            Document ID
        """
        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        self.documents_collection.add(
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
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search conversations with semantic similarity.

        Args:
            query: Search query
            agent_id: Filter by agent ID
            limit: Maximum results

        Returns:
            List of relevant conversations
        """
        where_filter = {"agent_id": agent_id} if agent_id else None

        results = self.conversations_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter
        )

        return self._format_results(results)

    async def search_agent_outputs(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search agent outputs.

        Args:
            query: Search query
            agent_id: Filter by agent ID
            limit: Maximum results

        Returns:
            List of relevant outputs
        """
        where_filter = {"agent_id": agent_id} if agent_id else None

        results = self.outputs_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter
        )

        return self._format_results(results)

    async def search_documents(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents for RAG.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant documents
        """
        results = self.documents_collection.query(
            query_texts=[query],
            n_results=limit
        )

        return self._format_results(results)

    async def get_conversation_history(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for an agent.

        Args:
            agent_id: Agent ID
            limit: Maximum messages

        Returns:
            List of conversations
        """
        results = self.conversations_collection.get(
            where={"agent_id": agent_id},
            limit=limit
        )

        if not results or not results["ids"]:
            return []

        formatted = []
        for i, doc_id in enumerate(results["ids"]):
            formatted.append({
                "id": doc_id,
                "message": results["documents"][i],
                "metadata": results["metadatas"][i]
            })

        # Sort by timestamp
        formatted.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)

        return formatted

    async def cleanup_old_memory(self, days: int = None):
        """
        Clean up old memory based on retention policy.

        Args:
            days: Days to retain (default from settings)
        """
        days = days or settings.memory_retention_days
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Note: ChromaDB doesn't have built-in time-based cleanup
        # This would need to be implemented with manual filtering
        # For now, this is a placeholder for future implementation

        return {"cutoff_date": cutoff_date, "status": "cleanup scheduled"}

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format ChromaDB query results."""
        if not results or not results["ids"]:
            return []

        formatted = []
        for i, doc_id in enumerate(results["ids"][0]):
            formatted.append({
                "id": doc_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })

        return formatted

    async def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "conversations_count": self.conversations_collection.count(),
            "outputs_count": self.outputs_collection.count(),
            "documents_count": self.documents_collection.count(),
            "retention_days": settings.memory_retention_days
        }


# Global memory service instance
memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    return memory_service
