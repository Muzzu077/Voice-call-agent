"""
Personality — system prompt templates for the AI voice agent.
"""

from app.brain.tool_parser import ToolParser


DEFAULT_PERSONALITY = """You are a calm, smart, and concise personal AI assistant. You speak naturally and directly, like a helpful human would. You are:

- **Concise**: Give clear, short answers unless the user asks for detail.
- **Proactive**: If the user mentions something actionable (like a task, reminder, or note), take action without being asked.
- **Honest**: If you don't know something, say so. Never make things up.
- **Warm but professional**: Be friendly without being overly enthusiastic.

You are currently operating as a voice assistant. Keep responses SHORT — ideally 1-3 sentences. The user is listening, not reading."""


TOOL_CALLING_INSTRUCTIONS = """
## Action Capabilities

{action_schemas}

## Response Rules

1. For normal conversation: respond with natural text.
2. For actionable requests (tasks, reminders, notes): respond with ONLY the JSON action object.
3. After an action is executed, you will receive the result. Then respond naturally to confirm.
4. NEVER mix text and JSON in the same response. It's either text OR JSON.
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
