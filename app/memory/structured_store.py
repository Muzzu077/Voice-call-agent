"""
SQLite structured store — manages tasks, reminders, call logs, and memory logs.
Uses aiosqlite for async operations.
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.memory.models import (
    Task, TaskCreate, TaskUpdate, TaskStatus,
    Reminder, ReminderCreate, ReminderStatus,
    CallLog, MemoryEntry,
)


class StructuredStore:
    """Async SQLite database manager for structured data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def init_db(self):
        """Create database and all tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS memory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                deadline TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                trigger_time TEXT NOT NULL,
                condition TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript TEXT,
                summary TEXT,
                actions_json TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT
            );
        """)
        await self._db.commit()

    async def close(self):
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    # ── Memory Logs ──────────────────────────────────────────

    async def save_memory_log(self, text: str, session_id: Optional[str] = None) -> int:
        """Save a conversation entry to memory_logs."""
        now = datetime.utcnow().isoformat()
        cursor = await self._db.execute(
            "INSERT INTO memory_logs (text, timestamp, session_id) VALUES (?, ?, ?)",
            (text, now, session_id),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_recent_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """Get the most recent memory log entries."""
        cursor = await self._db.execute(
            "SELECT * FROM memory_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            MemoryEntry(id=r["id"], text=r["text"], timestamp=r["timestamp"], session_id=r["session_id"])
            for r in reversed(rows)
        ]

    # ── Tasks ────────────────────────────────────────────────

    async def create_task(self, data: TaskCreate) -> Task:
        """Create a new task."""
        now = datetime.utcnow().isoformat()
        cursor = await self._db.execute(
            "INSERT INTO tasks (task, status, deadline, created_at) VALUES (?, ?, ?, ?)",
            (data.task, TaskStatus.PENDING.value, data.deadline, now),
        )
        await self._db.commit()
        return Task(
            id=cursor.lastrowid,
            task=data.task,
            status=TaskStatus.PENDING,
            deadline=data.deadline,
            created_at=now,
        )

    async def get_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get all tasks, optionally filtered by status."""
        if status:
            cursor = await self._db.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id DESC", (status.value,)
            )
        else:
            cursor = await self._db.execute("SELECT * FROM tasks ORDER BY id DESC")
        rows = await cursor.fetchall()
        return [
            Task(id=r["id"], task=r["task"], status=r["status"], deadline=r["deadline"], created_at=r["created_at"])
            for r in rows
        ]

    async def update_task(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        """Update a task's fields."""
        updates = []
        values = []
        if data.status is not None:
            updates.append("status = ?")
            values.append(data.status.value)
        if data.task is not None:
            updates.append("task = ?")
            values.append(data.task)
        if data.deadline is not None:
            updates.append("deadline = ?")
            values.append(data.deadline)

        if not updates:
            return None

        values.append(task_id)
        await self._db.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", values
        )
        await self._db.commit()

        cursor = await self._db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if row:
            return Task(id=row["id"], task=row["task"], status=row["status"], deadline=row["deadline"], created_at=row["created_at"])
        return None

    # ── Reminders ────────────────────────────────────────────

    async def create_reminder(self, data: ReminderCreate) -> Reminder:
        """Create a new reminder."""
        now = datetime.utcnow().isoformat()
        cursor = await self._db.execute(
            "INSERT INTO reminders (message, trigger_time, condition, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (data.message, data.trigger_time, data.condition, ReminderStatus.ACTIVE.value, now),
        )
        await self._db.commit()
        return Reminder(
            id=cursor.lastrowid,
            message=data.message,
            trigger_time=data.trigger_time,
            condition=data.condition,
            status=ReminderStatus.ACTIVE,
            created_at=now,
        )

    async def get_reminders(self, status: Optional[ReminderStatus] = None) -> List[Reminder]:
        """Get all reminders, optionally filtered by status."""
        if status:
            cursor = await self._db.execute(
                "SELECT * FROM reminders WHERE status = ? ORDER BY id DESC", (status.value,)
            )
        else:
            cursor = await self._db.execute("SELECT * FROM reminders ORDER BY id DESC")
        rows = await cursor.fetchall()
        return [
            Reminder(
                id=r["id"], message=r["message"], trigger_time=r["trigger_time"],
                condition=r["condition"], status=r["status"], created_at=r["created_at"],
            )
            for r in rows
        ]

    async def update_reminder_status(self, reminder_id: int, status: ReminderStatus) -> bool:
        """Update a reminder's status."""
        cursor = await self._db.execute(
            "UPDATE reminders SET status = ? WHERE id = ?",
            (status.value, reminder_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # ── Call Logs ────────────────────────────────────────────

    async def create_call_log(self, transcript: str = None, summary: str = None) -> CallLog:
        """Create a new call log entry."""
        now = datetime.utcnow().isoformat()
        cursor = await self._db.execute(
            "INSERT INTO calls (transcript, summary, started_at) VALUES (?, ?, ?)",
            (transcript, summary, now),
        )
        await self._db.commit()
        return CallLog(id=cursor.lastrowid, transcript=transcript, summary=summary, started_at=now)

    async def update_call_log(self, call_id: int, transcript: str = None, summary: str = None,
                               actions_json: str = None, ended_at: str = None) -> bool:
        """Update a call log entry."""
        updates = []
        values = []
        if transcript is not None:
            updates.append("transcript = ?")
            values.append(transcript)
        if summary is not None:
            updates.append("summary = ?")
            values.append(summary)
        if actions_json is not None:
            updates.append("actions_json = ?")
            values.append(actions_json)
        if ended_at is not None:
            updates.append("ended_at = ?")
            values.append(ended_at)

        if not updates:
            return False

        values.append(call_id)
        cursor = await self._db.execute(
            f"UPDATE calls SET {', '.join(updates)} WHERE id = ?", values
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def get_call_logs(self, limit: int = 20) -> List[CallLog]:
        """Get recent call logs."""
        cursor = await self._db.execute(
            "SELECT * FROM calls ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            CallLog(
                id=r["id"], transcript=r["transcript"], summary=r["summary"],
                actions_json=r["actions_json"], started_at=r["started_at"], ended_at=r["ended_at"],
            )
            for r in rows
        ]
