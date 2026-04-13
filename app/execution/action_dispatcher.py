"""
Action Dispatcher — routes parsed tool calls to the correct execution engine.
"""

import logging
from typing import Dict, Any, List, Optional

from app.memory.models import ActionResult

logger = logging.getLogger(__name__)


class ActionDispatcher:
    """Routes actions to their corresponding execution engines."""

    def __init__(self, memory_service=None):
        self._memory = memory_service
        self._task_engine = None
        self._reminder_engine = None

    def initialize(self, memory_service):
        """Initialize with memory service after it's ready."""
        from app.execution.task_engine import TaskEngine
        from app.execution.reminder_engine import ReminderEngine

        self._memory = memory_service
        self._task_engine = TaskEngine(memory_service)
        self._reminder_engine = ReminderEngine(memory_service)
        logger.info("Action dispatcher initialized with engines.")

    async def dispatch(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        Route an action to the correct execution engine.

        Args:
            action_data: Parsed action dict with 'action' key.

        Returns:
            ActionResult from the executed action.
        """
        action_name = action_data.get("action", "")
        logger.info(f"Dispatching action: {action_name}")

        handlers = {
            "create_task": self._handle_create_task,
            "create_reminder": self._handle_create_reminder,
            "save_note": self._handle_save_note,
            "make_call": self._handle_make_call,
        }

        handler = handlers.get(action_name)
        if handler is None:
            return ActionResult(
                success=False,
                message=f"Unknown action: '{action_name}'. Supported: {list(handlers.keys())}",
            )

        try:
            return await handler(action_data)
        except Exception as e:
            logger.error(f"Action '{action_name}' failed: {e}")
            return ActionResult(success=False, message=f"Action failed: {str(e)}")

    async def _handle_create_task(self, data: Dict[str, Any]) -> ActionResult:
        """Handle create_task action."""
        return await self._task_engine.create_task(
            task=data.get("task", ""),
            deadline=data.get("deadline"),
        )

    async def _handle_create_reminder(self, data: Dict[str, Any]) -> ActionResult:
        """Handle create_reminder action."""
        return await self._reminder_engine.create_reminder(
            message=data.get("message", ""),
            trigger_time=data.get("trigger_time", ""),
            condition=data.get("condition"),
        )

    async def _handle_save_note(self, data: Dict[str, Any]) -> ActionResult:
        """Handle save_note action — stores as a memory entry."""
        content = data.get("content", "")
        try:
            self._memory.vector_store.store_memory(
                text=f"Note: {content}",
                metadata={"type": "note"},
            )
            await self._memory.structured_store.save_memory_log(
                text=f"Note: {content}",
            )
            return ActionResult(
                success=True,
                message=f"Note saved: '{content}'",
                data={"content": content},
            )
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to save note: {str(e)}")

    async def _handle_make_call(self, data: Dict[str, Any]) -> ActionResult:
        """Handle make_call action — placeholder for Phase 4."""
        phone_number = data.get("phone_number", "")
        return ActionResult(
            success=False,
            message=f"Call to {phone_number} is not yet supported. Telephony integration is planned for Phase 4.",
            data={"phone_number": phone_number},
        )

    def get_supported_actions(self) -> List[str]:
        """Return list of supported action names."""
        return ["create_task", "create_reminder", "save_note", "make_call"]
