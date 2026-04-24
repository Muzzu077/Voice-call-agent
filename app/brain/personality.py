"""
Personality — system prompt templates for the AI voice agent.
"""

from app.brain.tool_parser import ToolParser


DEFAULT_PERSONALITY = """You are a concise voice assistant that controls the user's Windows computer.

RULES:
- Keep ALL responses to 1-2 sentences MAX. This is voice, not text.
- For actions: respond with ONLY a single JSON object. Nothing else.
- NEVER output multiple JSON objects. Pick the MOST important action.
- For "search X on YouTube": use search_browser with the full query.
- Understand Hinglish (Hindi+English mix) but always RESPOND in English."""


TOOL_CALLING_INSTRUCTIONS = """
## Action Capabilities

{action_schemas}

## Response Rules

1. For normal conversation: respond with natural text.
2. For actionable requests (tasks, reminders, notes, opening apps, searching, typing): respond with ONLY the JSON action object.
3. After an action is executed, you will receive the result. Then respond naturally to confirm.
4. NEVER mix text and JSON in the same response. It's either text OR JSON.
5. For desktop commands like "open chrome", "search youtube" — ALWAYS respond with JSON, never just acknowledge.
"""


class Personality:
    """Manages the AI agent's personality and system prompt."""

    def __init__(self, custom_personality: str = None):
        self.personality = custom_personality or DEFAULT_PERSONALITY

    def get_system_prompt(self) -> str:
        """Build the complete system prompt with personality + tool instructions."""
        action_schemas = ToolParser.get_action_schemas_description()
        tool_instructions = TOOL_CALLING_INSTRUCTIONS.format(action_schemas=action_schemas)

        return f"{self.personality}\n\n{tool_instructions}"

    def get_personality_only(self) -> str:
        """Get just the personality without tool instructions."""
        return self.personality

    def set_personality(self, personality: str):
        """Update the personality prompt."""
        self.personality = personality
