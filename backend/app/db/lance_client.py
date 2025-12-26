"""
ABOUTME: LanceDB client configuration and utilities.
ABOUTME: Provides embedded vector database with sentence-transformers embeddings.
"""

import logging
import os
from typing import Optional

import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize embedding model from registry
# Using sentence-transformers for local embeddings (no API calls needed)
_embedding_registry = get_registry()
_embedding_model = _embedding_registry.get("sentence-transformers").create(
    name="all-MiniLM-L6-v2",  # Fast, lightweight model (384 dimensions)
    device="cpu",
)


class ConversationSchema(LanceModel):
    """Schema for conversation memories."""

    id: str
    text: str = _embedding_model.SourceField()
    vector: Vector(_embedding_model.ndims()) = _embedding_model.VectorField()
    agent_id: str
    role: str
    timestamp: str
    # Additional metadata stored as JSON string
    metadata_json: Optional[str] = None


class AgentOutputSchema(LanceModel):
    """Schema for agent output memories."""

    id: str
    text: str = _embedding_model.SourceField()
    vector: Vector(_embedding_model.ndims()) = _embedding_model.VectorField()
    agent_id: str
    task_id: str
    timestamp: str
    metadata_json: Optional[str] = None


class DocumentSchema(LanceModel):
    """Schema for RAG documents."""

    id: str
    text: str = _embedding_model.SourceField()
    vector: Vector(_embedding_model.ndims()) = _embedding_model.VectorField()
    source: str
    timestamp: str
    metadata_json: Optional[str] = None


class LanceDBClient:
    """LanceDB client singleton for vector storage."""

    _instance = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._db is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize LanceDB client with persistent storage."""
        # Create LanceDB directory if it doesn't exist
        os.makedirs(settings.lance_db_path, exist_ok=True)

        # Initialize client with persistent storage
        self._db = lancedb.connect(settings.lance_db_path)
        logger.info(f"LanceDB initialized at {settings.lance_db_path}")

    @property
    def db(self):
        """Get LanceDB connection instance."""
        return self._db

    def get_or_create_table(self, name: str, schema: type[LanceModel]):
        """
        Get or create a table with the given schema.

        Args:
            name: Table name
            schema: Pydantic LanceModel schema class

        Returns:
            Table instance
        """
        try:
            # Try to open existing table
            return self._db.open_table(name)
        except Exception:
            # Create new table with schema
            logger.info(f"Creating new LanceDB table: {name}")
            return self._db.create_table(name, schema=schema)

    def delete_table(self, name: str):
        """
        Delete a table.

        Args:
            name: Table name to delete
        """
        try:
            self._db.drop_table(name)
            logger.info(f"Deleted LanceDB table: {name}")
        except Exception as e:
            logger.debug(f"Table deletion skipped: {e}")

    def list_tables(self) -> list[str]:
        """List all tables."""
        return self._db.table_names()

    def reset(self):
        """Reset all tables (use with caution)."""
        for table_name in self.list_tables():
            self.delete_table(table_name)
        logger.warning("All LanceDB tables have been reset")


# Global LanceDB client instance
lance_client = LanceDBClient()


def get_lance_client() -> LanceDBClient:
    """
    Dependency for getting LanceDB client.

    Returns:
        LanceDBClient instance
    """
    return lance_client


def get_embedding_model():
    """Get the embedding model for manual embedding if needed."""
    return _embedding_model
