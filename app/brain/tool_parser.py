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

# -- Productivity actions --

class CreateTaskAction(BaseModel):
    action: str  # "create_task"
    task: str
    deadline: Optional[str] = None

class CreateReminderAction(BaseModel):
    action: str  # "create_reminder"
    message: str
    trigger_time: str  # IST datetime, e.g. "2026-04-14T00:30:00"
    condition: Optional[str] = None

class SaveNoteAction(BaseModel):
    action: str  # "save_note"
    content: str

class MakeCallAction(BaseModel):
    action: str  # "make_call"
    phone_number: str
    message: Optional[str] = None

# -- Desktop automation actions --

class OpenAppAction(BaseModel):
    action: str  # "open_app"
    app: str  # e.g. "chrome", "vscode", "notepad"

class SearchBrowserAction(BaseModel):
    action: str  # "search_browser"
    query: str

class OpenUrlAction(BaseModel):
    action: str  # "open_url"
    url: str

class OpenFileAction(BaseModel):
    action: str  # "open_file"
    path: str

class TypeTextAction(BaseModel):
    action: str  # "type_text"
    text: str

class PressKeyAction(BaseModel):
    action: str  # "press_key"
    keys: str  # e.g. "ctrl+s", "alt+tab"

class ClickScreenAction(BaseModel):
    action: str  # "click_screen"
    x: int
    y: int


# ── Action Registry ─────────────────────────────────────────────

ACTION_SCHEMAS = {
    # Productivity
    "create_task": CreateTaskAction,
    "create_reminder": CreateReminderAction,
    "save_note": SaveNoteAction,
    "make_call": MakeCallAction,
    # Desktop automation
    "open_app": OpenAppAction,
    "search_browser": SearchBrowserAction,
    "open_url": OpenUrlAction,
    "open_file": OpenFileAction,
    "type_text": TypeTextAction,
    "press_key": PressKeyAction,
    "click_screen": ClickScreenAction,
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
        """Compact action descriptions for the system prompt."""
        return """ACTIONS (respond with ONE JSON object, no text):

{"action":"create_task","task":"text","deadline":"optional"}
{"action":"create_reminder","message":"text","trigger_time":"YYYY-MM-DDTHH:MM:SS in IST"}
{"action":"save_note","content":"text"}
{"action":"open_app","app":"chrome|vscode|notepad|explorer|terminal|calculator"}
{"action":"search_browser","query":"search terms"}
{"action":"open_url","url":"https://..."}
{"action":"open_file","path":"E:/path/to/file"}
{"action":"type_text","text":"text to type"}
{"action":"press_key","keys":"ctrl+s"}

REMINDER RULE: trigger_time MUST be absolute IST datetime. Calculate from current time."""

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
