"""
Reminder Engine — creates and manages time/condition-based reminders.
"""

import logging
from typing import Optional

from app.memory.models import ActionResult

logger = logging.getLogger(__name__)


class ReminderEngine:
    """Handles reminder creation and scheduling."""

    def __init__(self, memory_service):
        self.memory = memory_service

    async def create_reminder(self, message: str, trigger_time: str,
                               condition: Optional[str] = None) -> ActionResult:
        """
        Create a new reminder.

        Args:
            message: Reminder message.
            trigger_time: When to trigger (HH:MM or ISO datetime).
            condition: Optional trigger condition.

        Returns:
            ActionResult with success status and confirmation message.
        """
        try:
            result = await self.memory.save_reminder(
                message=message,
                trigger_time=trigger_time,
                condition=condition,
            )
            cond_msg = f" (condition: {condition})" if condition else ""
            msg = f"Reminder set: '{message}' at {trigger_time}{cond_msg}"
            logger.info(msg)
            return ActionResult(
                success=True,
                message=msg,
                data={
                    "reminder_id": result.id,
                    "message": message,
                    "trigger_time": trigger_time,
                    "condition": condition,
                },
            )
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
            return ActionResult(success=False, message=f"Failed to create reminder: {str(e)}")

    async def list_reminders(self) -> ActionResult:
        """List all active reminders."""
        try:
            reminders = await self.memory.get_reminders()
            if not reminders:
                return ActionResult(success=True, message="No reminders found.", data={"reminders": []})

            reminder_list = [
                {"id": r.id, "message": r.message, "trigger_time": r.trigger_time,
                 "status": r.status, "condition": r.condition}
                for r in reminders
            ]
            return ActionResult(
                success=True,
                message=f"Found {len(reminders)} reminder(s).",
                data={"reminders": reminder_list},
            )
        except Exception as e:
            logger.error(f"Failed to list reminders: {e}")
            return ActionResult(success=False, message=f"Failed to list reminders: {str(e)}")
