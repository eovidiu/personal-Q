"""
ChromaDB client configuration and utilities.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
import os

from config.settings import settings


class ChromaDBClient:
    """ChromaDB client singleton."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client with persistent storage."""
        # Create ChromaDB directory if it doesn't exist
        os.makedirs(settings.chroma_db_path, exist_ok=True)

        # Initialize client with persistent storage
        self._client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    @property
    def client(self):
        """Get ChromaDB client instance."""
        return self._client

    def get_or_create_collection(self, name: str, metadata: dict = None):
        """
        Get or create a collection.

        Args:
            name: Collection name
            metadata: Optional metadata for the collection

        Returns:
            Collection instance
        """
        # ChromaDB requires metadata to be non-empty if provided
        if metadata:
            return self._client.get_or_create_collection(
                name=name,
                metadata=metadata
            )
        else:
            return self._client.get_or_create_collection(name=name)

    def delete_collection(self, name: str):
        """
        Delete a collection.

        Args:
            name: Collection name to delete
        """
        try:
            self._client.delete_collection(name)
        except Exception:
            pass  # Collection doesn't exist

    def list_collections(self):
        """List all collections."""
        return self._client.list_collections()

    def reset(self):
        """Reset all collections (use with caution)."""
        self._client.reset()


# Global ChromaDB client instance
chroma_client = ChromaDBClient()


def get_chroma_client() -> ChromaDBClient:
    """
    Dependency for getting ChromaDB client.

    Returns:
        ChromaDBClient instance
    """
    return chroma_client
