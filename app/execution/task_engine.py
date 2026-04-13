"""
Task Engine — creates and manages tasks in SQLite.
"""

import logging
from typing import Optional

from app.memory.models import ActionResult

logger = logging.getLogger(__name__)


class TaskEngine:
    """Handles task creation and management."""

    def __init__(self, memory_service):
        self.memory = memory_service

    async def create_task(self, task: str, deadline: Optional[str] = None) -> ActionResult:
        """
        Create a new task.

        Args:
            task: Task description.
            deadline: Optional deadline string.

        Returns:
            ActionResult with success status and confirmation message.
        """
        try:
            result = await self.memory.save_task(task=task, deadline=deadline)
            deadline_msg = f" (deadline: {deadline})" if deadline else ""
            message = f"Task created: '{task}'{deadline_msg}"
            logger.info(message)
            return ActionResult(
                success=True,
                message=message,
                data={"task_id": result.id, "task": task, "deadline": deadline},
            )
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return ActionResult(success=False, message=f"Failed to create task: {str(e)}")

    async def list_tasks(self) -> ActionResult:
        """List all tasks."""
        try:
            tasks = await self.memory.get_tasks()
            if not tasks:
                return ActionResult(success=True, message="No tasks found.", data={"tasks": []})

            task_list = [{"id": t.id, "task": t.task, "status": t.status, "deadline": t.deadline} for t in tasks]
            return ActionResult(
                success=True,
                message=f"Found {len(tasks)} task(s).",
                data={"tasks": task_list},
            )
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return ActionResult(success=False, message=f"Failed to list tasks: {str(e)}")
