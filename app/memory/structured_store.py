"""
PostgreSQL structured store — manages tasks, reminders, call logs, and memory logs.
Uses SQLAlchemy for async operations and supports multi-tenancy via agent_id.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.database import AsyncSessionLocal
from app.db.models import Agent, Task as DBTask, Reminder as DBReminder, CallLog as DBCallLog, Conversation, ActionLog
from app.memory.models import (
    Task, TaskCreate, TaskUpdate, TaskStatus,
    Reminder, ReminderCreate, ReminderStatus,
    CallLog, MemoryEntry,
)


class StructuredStore:
    """Async PostgreSQL database manager for structured data."""

    def __init__(self, agent_id: Optional[UUID] = None):
        self.agent_id = agent_id

    async def _get_or_create_default_agent(self, session) -> UUID:
        """Fallback for legacy singleton usage. Creates a default agent if none exists."""
        if self.agent_id:
            return self.agent_id
            
        stmt = select(Agent).limit(1)
        result = await session.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if agent:
            self.agent_id = agent.id
            return agent.id
            
        # For legacy compatibility during migration - normally an error
        # Assuming a user exists or we create a dummy one?
        # A proper SaaS flow would require agent_id to be passed in explicitly.
        raise ValueError("Agent ID must be provided or an agent must exist in DB")

    async def init_db(self):
        """No-op as Alembic/main.py migrations handle table creation now."""
        pass

    async def close(self):
        """No-op as connection pooling handles this."""
        pass

    # ── Memory Logs ──────────────────────────────────────────

    async def save_memory_log(self, text: str, session_id: Optional[str] = None) -> str:
        """Save a conversation entry to conversations."""
        async with AsyncSessionLocal() as session:
            agent_id = await self._get_or_create_default_agent(session)
            conv = Conversation(
                agent_id=agent_id,
                session_id=session_id,
                user_message="[System/Note]", 
                ai_response=text
            )
            session.add(conv)
            await session.commit()
            return str(conv.id)

    async def get_recent_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """Get the most recent memory log entries."""
        async with AsyncSessionLocal() as session:
            agent_id = await self._get_or_create_default_agent(session)
            stmt = select(Conversation).where(Conversation.agent_id == agent_id).order_by(desc(Conversation.created_at)).limit(limit)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                MemoryEntry(
                    id=0, # Legacy int ID placeholder
                    text=f"{r.user_message}: {r.ai_response}",
                    timestamp=r.created_at.isoformat(),
                    session_id=r.session_id
                )
                for r in reversed(rows)
            ]

    # ── Tasks ────────────────────────────────────────────────

    async def create_task(self, data: TaskCreate) -> Task:
        async with AsyncSessionLocal() as session:
            agent_id = await self._get_or_create_default_agent(session)
            db_task = DBTask(
                agent_id=agent_id,
                task=data.task,
                status=TaskStatus.PENDING.value,
                deadline=data.deadline
            )
            session.add(db_task)
            await session.commit()
            await session.refresh(db_task)
            return Task(
                id=db_task.id,
                task=db_task.task,
                status=TaskStatus(db_task.status),
                deadline=db_task.deadline,
                created_at=db_task.created_at.isoformat()
            )

    async def get_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        async with AsyncSessionLocal() as session:
            try:
                agent_id = await self._get_or_create_default_agent(session)
            except ValueError:
                return []
            stmt = select(DBTask).where(DBTask.agent_id == agent_id)
            if status:
                stmt = stmt.where(DBTask.status == status.value)
            stmt = stmt.order_by(desc(DBTask.id))
            
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                Task(
                    id=r.id, task=r.task, status=TaskStatus(r.status),
                    deadline=r.deadline, created_at=r.created_at.isoformat()
                )
                for r in rows
            ]

    async def update_task(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        async with AsyncSessionLocal() as session:
            stmt = select(DBTask).where(DBTask.id == task_id)
            result = await session.execute(stmt)
            db_task = result.scalar_one_or_none()
            
            if not db_task:
                return None
                
            if data.status is not None:
                db_task.status = data.status.value
            if data.task is not None:
                db_task.task = data.task
            if data.deadline is not None:
                db_task.deadline = data.deadline
                
            await session.commit()
            await session.refresh(db_task)
            
            return Task(
                id=db_task.id, task=db_task.task, status=TaskStatus(db_task.status),
                deadline=db_task.deadline, created_at=db_task.created_at.isoformat()
            )

    # ── Reminders ────────────────────────────────────────────

    async def create_reminder(self, data: ReminderCreate) -> Reminder:
        async with AsyncSessionLocal() as session:
            agent_id = await self._get_or_create_default_agent(session)
            db_rem = DBReminder(
                agent_id=agent_id,
                message=data.message,
                trigger_time=data.trigger_time,
                condition=data.condition,
                status=ReminderStatus.ACTIVE.value
            )
            session.add(db_rem)
            await session.commit()
            await session.refresh(db_rem)
            return Reminder(
                id=db_rem.id, message=db_rem.message, trigger_time=db_rem.trigger_time,
                condition=db_rem.condition, status=ReminderStatus(db_rem.status),
                created_at=db_rem.created_at.isoformat()
            )

    async def get_reminders(self, status: Optional[ReminderStatus] = None) -> List[Reminder]:
        async with AsyncSessionLocal() as session:
            try:
                agent_id = await self._get_or_create_default_agent(session)
            except ValueError:
                return []
            stmt = select(DBReminder).where(DBReminder.agent_id == agent_id)
            if status:
                stmt = stmt.where(DBReminder.status == status.value)
            stmt = stmt.order_by(desc(DBReminder.id))
            
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                Reminder(
                    id=r.id, message=r.message, trigger_time=r.trigger_time,
                    condition=r.condition, status=ReminderStatus(r.status),
                    created_at=r.created_at.isoformat()
                )
                for r in rows
            ]

    async def update_reminder_status(self, reminder_id: int, status: ReminderStatus) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = select(DBReminder).where(DBReminder.id == reminder_id)
            result = await session.execute(stmt)
            db_rem = result.scalar_one_or_none()
            
            if not db_rem:
                return False
                
            db_rem.status = status.value
            await session.commit()
            return True

    # ── Call Logs ────────────────────────────────────────────

    async def create_call_log(self, transcript: str = None, summary: str = None) -> CallLog:
        async with AsyncSessionLocal() as session:
            agent_id = await self._get_or_create_default_agent(session)
            db_call = DBCallLog(agent_id=agent_id, transcript=transcript, summary=summary)
            session.add(db_call)
            await session.commit()
            await session.refresh(db_call)
            return CallLog(
                id=db_call.id, transcript=db_call.transcript, summary=db_call.summary,
                started_at=db_call.started_at.isoformat()
            )

    async def update_call_log(self, call_id: int, transcript: str = None, summary: str = None,
                               actions_json: str = None, ended_at: str = None) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = select(DBCallLog).where(DBCallLog.id == call_id)
            result = await session.execute(stmt)
            db_call = result.scalar_one_or_none()
            
            if not db_call:
                return False
                
            if transcript is not None:
                db_call.transcript = transcript
            if summary is not None:
                db_call.summary = summary
            if actions_json is not None:
                try:
                    import json
                    db_call.actions_json = json.loads(actions_json) if isinstance(actions_json, str) else actions_json
                except:
                    pass
            if ended_at is not None:
                from datetime import datetime
                try:
                    db_call.ended_at = datetime.fromisoformat(ended_at)
                except:
                    pass
                    
            await session.commit()
            return True

    async def get_call_logs(self, limit: int = 20) -> List[CallLog]:
        async with AsyncSessionLocal() as session:
            try:
                agent_id = await self._get_or_create_default_agent(session)
            except ValueError:
                return []
            stmt = select(DBCallLog).where(DBCallLog.agent_id == agent_id).order_by(desc(DBCallLog.id)).limit(limit)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                CallLog(
                    id=r.id, transcript=r.transcript, summary=r.summary,
                    actions_json=str(r.actions_json) if r.actions_json else None,
                    started_at=r.started_at.isoformat(),
                    ended_at=r.ended_at.isoformat() if r.ended_at else None
                )
                for r in rows
            ]
