"""
Context Builder — dynamically assembles prompts from memory, history, and personality.
"""

import logging
from typing import List, Optional

from app.brain.personality import Personality

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds the LLM prompt by combining personality, memory, and conversation history."""

    def __init__(self, personality: Optional[Personality] = None):
        self.personality = personality or Personality()
        self._short_term_memory: List[dict] = []  # Recent conversation turns
        self._max_short_term = 20  # Max turns to keep in memory

    def build_system_prompt(self) -> str:
        """Build the system prompt with personality + tool instructions."""
        return self.personality.get_system_prompt()

    def build_context(
        self,
        user_message: str,
        relevant_memories: Optional[List[str]] = None,
        history: Optional[List[dict]] = None,
    ) -> tuple[str, List[dict]]:
        """
        Build full context for the LLM call.

        Args:
            user_message: Current user input.
            relevant_memories: Retrieved memories from vector store.
            history: Override conversation history (uses short-term if None).

        Returns:
            Tuple of (system_prompt, conversation_history).
        """
        system_prompt = self.build_system_prompt()

        # Inject relevant memories into system prompt if available
        if relevant_memories:
            memory_context = "\n## Relevant Context from Past Conversations\n"
            for i, mem in enumerate(relevant_memories[:5], 1):
                memory_context += f"{i}. {mem}\n"
            memory_context += "\nUse this context if relevant to the current conversation.\n"
            system_prompt += memory_context

        # Use provided history or short-term memory
        conv_history = history if history is not None else list(self._short_term_memory)

        return system_prompt, conv_history

    def add_turn(self, role: str, content: str):
        """
        Add a conversation turn to short-term memory.

        Args:
            role: "user" or "assistant"
            content: The message content
        """
        self._short_term_memory.append({"role": role, "content": content})

        # Trim if too long
        if len(self._short_term_memory) > self._max_short_term:
            self._short_term_memory = self._short_term_memory[-self._max_short_term:]

    def get_history(self) -> List[dict]:
        """Get current short-term conversation history."""
        return list(self._short_term_memory)

    def clear_history(self):
        """Clear short-term memory."""
        self._short_term_memory.clear()

    def get_history_text(self) -> str:
        """Get conversation history as a formatted string."""
        lines = []
        for turn in self._short_term_memory:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)
