"""
Reminder routes — /reminders endpoints for reminder management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reminders", tags=["Reminders"])

_agent = None


def set_agent(agent):
    """Inject the agent service instance."""
    global _agent
    _agent = agent


class ReminderCreateRequest(BaseModel):
    message: str
    trigger_time: str
    condition: Optional[str] = None


@router.post("/")
async def create_reminder(request: ReminderCreateRequest):
    """Create a new reminder."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.memory.save_reminder(
            message=request.message,
            trigger_time=request.trigger_time,
            condition=request.condition,
        )
        return {"success": True, "reminder": result.model_dump()}
    except Exception as e:
        logger.error(f"Reminder creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_reminders():
    """List all reminders."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        reminders = await _agent.memory.get_reminders()
        return {"reminders": [r.model_dump() for r in reminders]}
    except Exception as e:
        logger.error(f"Reminder list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
