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
        self._desktop_engine = None

    def initialize(self, memory_service):
        """Initialize with memory service after it's ready."""
        from app.execution.task_engine import TaskEngine
        from app.execution.reminder_engine import ReminderEngine
        from app.automation.desktop_engine import DesktopEngine

        self._memory = memory_service
        self._task_engine = TaskEngine(memory_service)
        self._reminder_engine = ReminderEngine(memory_service)
        self._desktop_engine = DesktopEngine()
        logger.info("Action dispatcher initialized with engines (tasks, reminders, desktop).")

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

        # Productivity handlers
        productivity_handlers = {
            "create_task": self._handle_create_task,
            "create_reminder": self._handle_create_reminder,
            "save_note": self._handle_save_note,
            "make_call": self._handle_make_call,
        }

        # Desktop automation actions — routed directly to DesktopEngine
        desktop_actions = {
            "open_app", "search_browser", "open_url",
            "open_file", "type_text", "press_key", "click_screen",
        }

        # Check productivity first
        handler = productivity_handlers.get(action_name)
        if handler is not None:
            try:
                return await handler(action_data)
            except Exception as e:
                logger.error(f"Action '{action_name}' failed: {e}")
                return ActionResult(success=False, message=f"Action failed: {str(e)}")

        # Check desktop automation
        if action_name in desktop_actions:
            if self._desktop_engine is None:
                return ActionResult(success=False, message="Desktop engine not initialized.")
            try:
                return await self._desktop_engine.execute(action_data)
            except Exception as e:
                logger.error(f"Desktop action '{action_name}' failed: {e}")
                return ActionResult(success=False, message=f"Desktop action failed: {str(e)}")

        return ActionResult(
            success=False,
            message=f"Unknown action: '{action_name}'. Supported: {self.get_supported_actions()}",
        )

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
        """Handle make_call action — uses Twilio to place outbound call."""
        phone_number = data.get("phone_number", "")
        message = data.get("message", "Hello from your AI assistant.")

        from app.config import settings
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            return ActionResult(
                success=False,
                message="Twilio not configured. Cannot place calls.",
            )

        try:
            from app.execution.scheduler import _get_public_url, _fire_reminder_sync
            import asyncio

            public_url = _get_public_url()
            if not public_url:
                return ActionResult(success=False, message="No ngrok URL — cannot place call.")

            call_sid = await asyncio.to_thread(
                _fire_reminder_sync, message, public_url
            )
            return ActionResult(
                success=True,
                message=f"Call placed to {phone_number}. SID: {call_sid}",
                data={"phone_number": phone_number, "call_sid": call_sid},
            )
        except Exception as e:
            return ActionResult(success=False, message=f"Call failed: {str(e)}")

    def get_supported_actions(self) -> List[str]:
        """Return list of supported action names."""
        return [
            "create_task", "create_reminder", "save_note", "make_call",
            "open_app", "search_browser", "open_url",
            "open_file", "type_text", "press_key", "click_screen",
        ]
