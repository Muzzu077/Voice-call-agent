"""
Rolling Summary Engine — compresses conversation history to prevent context bloat.
Every N messages, the oldest turns are summarized into a condensed paragraph,
keeping the LLM prompt lean and fast for sub-second responses.
"""

import logging
from typing import List

from app.brain.llm_engine import LLMEngine

logger = logging.getLogger(__name__)

COMPRESSION_THRESHOLD = 10  # Compress after this many turns
KEEP_RECENT = 4  # Always keep the last N turns uncompressed

SUMMARIZE_PROMPT = """Summarize the following conversation history into 2-3 concise sentences.
Focus on: key topics discussed, any actions performed, and important context.
Do NOT include greetings or filler. Be factual and brief.

Conversation:
{conversation}

Summary:"""


class SummaryEngine:
    """Compresses old conversation history into rolling summaries."""

    def __init__(self):
        self.llm = LLMEngine()
        self._rolling_summary: str = ""

    @property
    def has_summary(self) -> bool:
        return bool(self._rolling_summary)

    @property
    def summary(self) -> str:
        return self._rolling_summary

    async def maybe_compress(self, history: List[dict]) -> List[dict]:
        """
        Check if history is long enough to compress.
        Returns a (possibly shorter) history list.

        If len(history) >= COMPRESSION_THRESHOLD:
        1. Take the oldest turns (all except the last KEEP_RECENT)
        2. Summarize them via LLM
        3. Prepend summary as a system-like context message
        4. Return only the recent turns
        """
        if len(history) < COMPRESSION_THRESHOLD:
            return history

        logger.info(
            f"📦 Compressing {len(history)} turns (keeping last {KEEP_RECENT})"
        )

        # Split into old (to compress) and recent (to keep)
        old_turns = history[:-KEEP_RECENT]
        recent_turns = history[-KEEP_RECENT:]

        # Format old turns for summarization
        conversation_text = "\n".join(
            f"{'User' if t['role'] == 'user' else 'Assistant'}: {t['content']}"
            for t in old_turns
        )

        # Add existing rolling summary if we have one
        if self._rolling_summary:
            conversation_text = (
                f"Previous context: {self._rolling_summary}\n\n{conversation_text}"
            )

        # Summarize via LLM
        try:
            prompt = SUMMARIZE_PROMPT.format(conversation=conversation_text)
            summary = await self.llm.chat(
                user_message=prompt,
                system_prompt="You are a concise summarizer. Output only the summary, nothing else.",
            )
            self._rolling_summary = summary.strip()
            logger.info(
                f"✅ Summary: '{self._rolling_summary[:80]}...'"
            )
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # On failure, just trim old turns without summary
            return recent_turns

        # Prepend summary as context
        summary_turn = {
            "role": "system",
            "content": f"[Previous conversation summary: {self._rolling_summary}]",
        }

        return [summary_turn] + recent_turns

    def reset(self):
        """Clear the rolling summary."""
        self._rolling_summary = ""
