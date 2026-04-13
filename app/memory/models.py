"""
Data models for the Voice Call AI Agent.
Pydantic models for tasks, reminders, call logs, and memory entries.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReminderStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"


# ── Task Models ──────────────────────────────────────────────────

class TaskCreate(BaseModel):
    task: str
    deadline: Optional[str] = None

class Task(BaseModel):
    id: int
    task: str
    status: TaskStatus = TaskStatus.PENDING
    deadline: Optional[str] = None
    created_at: str

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    task: Optional[str] = None
    deadline: Optional[str] = None


# ── Reminder Models ─────────────────────────────────────────────

class ReminderCreate(BaseModel):
    message: str
    trigger_time: str
    condition: Optional[str] = None

class Reminder(BaseModel):
    id: int
    message: str
    trigger_time: str
    condition: Optional[str] = None
    status: ReminderStatus = ReminderStatus.ACTIVE
    created_at: str


# ── Call Log Models ──────────────────────────────────────────────

class CallLog(BaseModel):
    id: int
    transcript: Optional[str] = None
    summary: Optional[str] = None
    actions_json: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None


# ── Memory Models ────────────────────────────────────────────────

class MemoryEntry(BaseModel):
    id: int
    text: str
    timestamp: str
    session_id: Optional[str] = None


# ── Chat Models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    action: Optional[dict] = None
    action_result: Optional[str] = None


# ── Action Models ────────────────────────────────────────────────

class ActionResult(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
