"""
Audio Output Manager — manages TTS playback and barge-in coordination with VAD.
Provides the bridge between agent responses and speaker output.
"""

import asyncio
import logging
from typing import Callable, Optional

from app.output.tts_engine import TTSEngine

logger = logging.getLogger(__name__)


class AudioOutput:
    """
    Manages audio output with barge-in support.

    Responsibilities:
    1. Receive text responses from agent
    2. Send to TTS for synthesis
    3. Play audio through speaker
    4. Stop immediately on VAD interrupt signal
    5. Report speaking state to AudioPipeline (for barge-in detection)
    """

    def __init__(self, tts_engine: Optional[TTSEngine] = None):
        self._tts = tts_engine or TTSEngine()
        self._speaking = False
        self._on_speaking_start: Optional[Callable] = None
        self._on_speaking_stop: Optional[Callable] = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start the TTS engine."""
        self._tts.start()

    def stop(self):
        """Stop all output."""
        self._tts.stop()
        self._speaking = False

    # ── Callbacks ────────────────────────────────────────────────

    def on_speaking_start(self, callback: Callable):
        """Called when AI starts speaking."""
        self._on_speaking_start = callback

    def on_speaking_stop(self, callback: Callable):
        """Called when AI stops speaking (finished or interrupted)."""
        self._on_speaking_stop = callback

    # ── Output API ───────────────────────────────────────────────

    async def speak(self, text: str):
        """
        Speak the given text. Returns when done or interrupted.

        Args:
            text: Response text to synthesize and play.
        """
        if not text or not text.strip():
            return

        self._speaking = True
        await self._fire(self._on_speaking_start)

        try:
            await self._tts.speak(text)
        finally:
            self._speaking = False
            await self._fire(self._on_speaking_stop)

    async def stream(self, text: str):
        """
        Synthesize text and yield audio chunks without playing them locally.
        Useful for sending audio over WebSockets (e.g., Twilio).

        Args:
            text: Response text to synthesize.

        Yields:
            np.ndarray of float32 audio samples.
        """
        if not text or not text.strip():
            return

        self._speaking = True
        await self._fire(self._on_speaking_start)

        try:
            async for chunk in self._tts.synthesize_stream(text):
                yield chunk
        finally:
            self._speaking = False
            await self._fire(self._on_speaking_stop)

    def interrupt(self):
        """
        Immediately stop current audio playback (barge-in).
        Called by VAD when user speech is detected.
        """
        if self._speaking:
            logger.info("AudioOutput: Interrupting playback (barge-in).")
            self._tts.interrupt()
            self._speaking = False

    # ── State ────────────────────────────────────────────────────

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    # ── Helpers ──────────────────────────────────────────────────

    async def _fire(self, callback: Optional[Callable]):
        if callback is None:
            return
        if asyncio.iscoroutinefunction(callback):
            await callback()
        else:
            callback()
