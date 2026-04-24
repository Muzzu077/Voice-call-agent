"""
Memory Service — unified interface over vector (ChromaDB) and structured (PostgreSQL) stores.
Supports multi-tenancy via agent_id.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.memory.vector_store import VectorStore
from app.memory.structured_store import StructuredStore
from app.memory.models import TaskCreate, ReminderCreate, Task, Reminder

logger = logging.getLogger(__name__)


class MemoryService:
    """Unified memory interface combining vector and structured storage."""

    def __init__(self, agent_id: Optional[UUID] = None):
        self.agent_id = agent_id
        self.vector_store = VectorStore(agent_id=agent_id)
        self.structured_store = StructuredStore(agent_id=agent_id)
        self._initialized = False

    async def initialize(self):
        """Initialize both storage backends."""
        if self._initialized:
            return

        # Initialize ChromaDB (sync)
        self.vector_store.init()

        # Initialize SQLite/Postgres schemas (now handled by main app startup)
        # We just need to make sure connections work
        await self.structured_store.init_db()

        self._initialized = True
        logger.info(f"Memory service initialized for agent {self.agent_id} (ChromaDB + PostgreSQL).")

    async def shutdown(self):
        """Gracefully close connections."""
        await self.structured_store.close()
        logger.info("Memory service shut down.")

    # ── Conversation Memory ──────────────────────────────────

    async def save_conversation(self, user_message: str, ai_response: str,
                                 session_id: Optional[str] = None):
        # Format for vector storage
        conversation_text = f"User: {user_message}\nAssistant: {ai_response}"

        # Store in ChromaDB for semantic search
        self.vector_store.store_memory(
            text=conversation_text,
            metadata={"session_id": session_id or "default", "type": "conversation"},
        )

        # Store in Postgres for structured access
        await self.structured_store.save_memory_log(
            text=conversation_text,
            session_id=session_id,
        )

        logger.debug(f"Conversation saved. Vector count: {self.vector_store.get_count()}")

    async def recall_context(self, query: str, top_k: int = 5) -> List[str]:
        if self.vector_store.get_count() == 0:
            return []

        memories = self.vector_store.search_similar(query, top_k=top_k)
        return [m["text"] for m in memories if m.get("text")]

    async def get_recent_history(self, n: int = 10) -> List[dict]:
        entries = await self.structured_store.get_recent_memories(limit=n)
        return [{"text": e.text, "timestamp": e.timestamp} for e in entries]

    # ── Task Operations ──────────────────────────────────────

    async def save_task(self, task: str, deadline: Optional[str] = None) -> Task:
        data = TaskCreate(task=task, deadline=deadline)
        return await self.structured_store.create_task(data)

    async def get_tasks(self) -> List[Task]:
        return await self.structured_store.get_tasks()

    # ── Reminder Operations ──────────────────────────────────

    async def save_reminder(self, message: str, trigger_time: str,
                            condition: Optional[str] = None) -> Reminder:
        data = ReminderCreate(message=message, trigger_time=trigger_time, condition=condition)
        return await self.structured_store.create_reminder(data)

    async def get_reminders(self) -> List[Reminder]:
        return await self.structured_store.get_reminders()

    # ── Stats ────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "vector_memories": self.vector_store.get_count(),
            "initialized": self._initialized,
            "agent_id": str(self.agent_id) if self.agent_id else None
        }
