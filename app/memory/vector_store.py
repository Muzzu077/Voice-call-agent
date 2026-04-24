"""
ChromaDB Vector Store — semantic memory for conversation recall.
Supports multi-tenancy via per-agent collections.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB wrapper for semantic conversation memory."""

    def __init__(self, agent_id: Optional[UUID] = None):
        self.agent_id = agent_id
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None

    @property
    def collection_name(self) -> str:
        """Get the unique collection name for this agent."""
        if self.agent_id:
            # ChromaDB collection names must be valid: contain only chars, numbers, underscores
            clean_id = str(self.agent_id).replace("-", "_")
            return f"agent_{clean_id}_memory"
        return "conversation_memory"  # Legacy single-user fallback

    def init(self):
        """Initialize ChromaDB HTTP client and create/load collection."""
        try:
            # Fallback for local dev if host/port aren't resolving
            try:
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                # Test connection
                self._client.heartbeat()
            except Exception as e:
                logger.warning(f"Could not connect to ChromaDB via HTTP ({settings.CHROMA_HOST}:{settings.CHROMA_PORT}). Falling back to local PersistentClient: {e}")
                self._client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIR,
                )

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            count = self._collection.count()
            logger.info(f"ChromaDB initialized. Collection '{self.collection_name}' has {count} entries.")
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    def store_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None,
                     doc_id: Optional[str] = None) -> str:
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
        if self._collection is None:
            return 0
        return self._collection.count()

    def delete_memory(self, doc_id: str) -> bool:
        if self._collection is None:
            return False
        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {doc_id}: {e}")
            return False

    def clear_all(self):
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"All memories cleared for {self.collection_name}.")
            except Exception as e:
                logger.error(f"Failed to clear memories: {e}")
