"""
Tool Parser — detects and extracts structured JSON tool calls from LLM output.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# ── Action Schemas ───────────────────────────────────────────────

class CreateTaskAction(BaseModel):
    action: str  # "create_task"
    task: str
    deadline: Optional[str] = None

class CreateReminderAction(BaseModel):
    action: str  # "create_reminder"
    message: str
    trigger_time: str  # e.g., "18:00" or "2026-04-14T18:00:00"
    condition: Optional[str] = None

class SaveNoteAction(BaseModel):
    action: str  # "save_note"
    content: str

class MakeCallAction(BaseModel):
    action: str  # "make_call"
    phone_number: str
    message: Optional[str] = None


# ── Action Registry ─────────────────────────────────────────────

ACTION_SCHEMAS = {
    "create_task": CreateTaskAction,
    "create_reminder": CreateReminderAction,
    "save_note": SaveNoteAction,
    "make_call": MakeCallAction,
}


class ToolParser:
    """Parses LLM output to detect and validate JSON tool calls."""

    @staticmethod
    def is_tool_call(text: str) -> bool:
        """
        Check if the LLM output contains a JSON tool call.
        Handles raw JSON, markdown-wrapped JSON, and mixed text+JSON.
        """
        cleaned = ToolParser._extract_json_string(text)
        if cleaned is None:
            return False

        try:
            data = json.loads(cleaned)
            return isinstance(data, dict) and "action" in data
        except (json.JSONDecodeError, TypeError):
            return False

    @staticmethod
    def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract and validate a tool call from LLM output.

        Returns:
            Validated action dict, or None if not a valid tool call.
        """
        cleaned = ToolParser._extract_json_string(text)
        if cleaned is None:
            return None

        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            return None

        if not isinstance(data, dict) or "action" not in data:
            return None

        action_name = data.get("action", "")
        schema = ACTION_SCHEMAS.get(action_name)

        if schema is None:
            logger.warning(f"Unknown action: {action_name}")
            return None

        try:
            validated = schema(**data)
            return validated.model_dump()
        except ValidationError as e:
            logger.warning(f"Action validation failed for '{action_name}': {e}")
            return None

    @staticmethod
    def get_supported_actions() -> List[str]:
        """Return list of supported action names."""
        return list(ACTION_SCHEMAS.keys())

    @staticmethod
    def get_action_schemas_description() -> str:
        """
        Generate a description of all supported actions for the system prompt.
        This tells the LLM what JSON structures it can output.
        """
        descriptions = []
        descriptions.append("You can perform actions by responding with ONLY a JSON object (no other text).")
        descriptions.append("Supported actions:\n")

        descriptions.append("""1. Create a task:
{"action": "create_task", "task": "description of the task", "deadline": "optional deadline"}

2. Create a reminder:
{"action": "create_reminder", "message": "reminder message", "trigger_time": "HH:MM or ISO datetime", "condition": "optional condition"}

3. Save a note:
{"action": "save_note", "content": "note content"}

4. Make a call (future):
{"action": "make_call", "phone_number": "+1234567890", "message": "optional message"}""")

        descriptions.append("\nIMPORTANT: When performing an action, respond with ONLY the JSON object. Do not include any other text before or after the JSON.")
        return "\n".join(descriptions)

    @staticmethod
    def _extract_json_string(text: str) -> Optional[str]:
        """
        Extract JSON string from text, handling:
        - Raw JSON
        - Markdown code blocks (```json ... ```)
        - Leading/trailing whitespace
        """
        if not text or not text.strip():
            return None

        text = text.strip()

        # Try markdown code block extraction first
        json_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(json_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try to find JSON object directly
        # Look for the first { and last } to extract potential JSON
        first_brace = text.find("{")
        last_brace = text.rfind("}")

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = text[first_brace : last_brace + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # Return the raw text if it might be JSON
        if text.startswith("{"):
            return text

        return None
