"""
ChromaDB Vector Store — semantic memory for conversation recall.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB wrapper for semantic conversation memory."""

    COLLECTION_NAME = "conversation_memory"

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None

    def init(self):
        """Initialize ChromaDB client and create/load collection."""
        try:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
            )
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            count = self._collection.count()
            logger.info(f"ChromaDB initialized. Collection '{self.COLLECTION_NAME}' has {count} entries.")
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    def store_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None,
                     doc_id: Optional[str] = None) -> str:
        """
        Store a conversation entry in the vector database.

        Args:
            text: The conversation text to store.
            metadata: Additional metadata (timestamp, session_id, etc.)
            doc_id: Optional custom document ID.

        Returns:
            The document ID used for storage.
        """
        if self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call init() first.")

        if doc_id is None:
            doc_id = f"mem_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        if metadata is None:
            metadata = {}

        metadata["timestamp"] = datetime.utcnow().isoformat()

        try:
            self._collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id],
            )
            logger.debug(f"Stored memory: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for memories similar to the query.

        Args:
            query: The text to search for.
            top_k: Number of results to return.

        Returns:
            List of dicts with 'text', 'metadata', 'distance' keys.
        """
        if self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call init() first.")

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, self._collection.count()) if self._collection.count() > 0 else 1,
            )

            memories = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    memory = {
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                        "id": results["ids"][0][i] if results["ids"] else "",
                    }
                    memories.append(memory)

            return memories
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    def get_count(self) -> int:
        """Get the total number of memories stored."""
        if self._collection is None:
            return 0
        return self._collection.count()

    def delete_memory(self, doc_id: str) -> bool:
        """Delete a specific memory by ID."""
        if self._collection is None:
            return False
        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {doc_id}: {e}")
            return False

    def clear_all(self):
        """Delete all memories (use with caution)."""
        if self._client:
            try:
                self._client.delete_collection(self.COLLECTION_NAME)
                self._collection = self._client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("All memories cleared.")
            except Exception as e:
                logger.error(f"Failed to clear memories: {e}")
