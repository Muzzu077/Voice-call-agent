"""
Task routes — /tasks endpoints for task management.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

_agent = None


def set_agent(agent):
    """Inject the agent service instance."""
    global _agent
    _agent = agent


class TaskCreateRequest(BaseModel):
    task: str
    deadline: Optional[str] = None


@router.post("/")
async def create_task(request: TaskCreateRequest):
    """Create a new task."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.memory.save_task(task=request.task, deadline=request.deadline)
        return {"success": True, "task": result.model_dump()}
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tasks():
    """List all tasks."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        tasks = await _agent.memory.get_tasks()
        return {"tasks": [t.model_dump() for t in tasks]}
    except Exception as e:
        logger.error(f"Task list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
