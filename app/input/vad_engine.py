"""
VAD Engine — real-time voice activity detection using Silero VAD Lite (ONNX).
Detects speech start/end and barge-in interruptions.
"""

import asyncio
import logging
import numpy as np
from enum import Enum
from typing import Callable, Optional, Awaitable

from silero_vad_lite import SileroVAD

from app.config import settings

logger = logging.getLogger(__name__)


class SpeechState(Enum):
    SILENCE = "silence"
    SPEECH = "speech"


class VADEngine:
    """
    Real-time voice activity detection using Silero VAD Lite.

    State machine:
        SILENCE → SPEECH  : on_speech_start() callback + STT trigger
        SPEECH  → SILENCE : on_speech_end() callback + STT finalize
        SPEECH  → SPEECH  : interrupt detected → on_interrupt() callback
    """

    # Silero VAD only supports 8000 or 16000 Hz
    SUPPORTED_SAMPLE_RATES = (8000, 16000)

    def __init__(
        self,
        sample_rate: int = None,
        threshold: float = None,
        silence_duration_ms: int = 600,
    ):
        self.sample_rate = sample_rate or settings.AUDIO_SAMPLE_RATE
        self.threshold = threshold or settings.VAD_THRESHOLD
        self.silence_duration_ms = silence_duration_ms  # ms of silence before speech_end fires

        if self.sample_rate not in self.SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Sample rate {self.sample_rate} not supported. Use 8000 or 16000.")

        self._vad: Optional[SileroVAD] = None
        self._state = SpeechState.SILENCE
        self._silence_frames = 0
        self._frames_per_ms = self.sample_rate / 1000

        # Silero VAD requires exactly this many samples per process() call
        self.WINDOW_SIZE = 512
        # Accumulator for incoming audio that may arrive in non-512 chunks
        self._chunk_buffer = np.array([], dtype=np.float32)

        # Callbacks
        self._on_speech_start: Optional[Callable] = None
        self._on_speech_end: Optional[Callable] = None
        self._on_interrupt: Optional[Callable] = None

        self._running = False

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Initialize the VAD model."""
        if self._vad is None:
            self._vad = SileroVAD(self.sample_rate)
            logger.info(f"VAD engine started (sample_rate={self.sample_rate}, threshold={self.threshold})")
        self._running = True

    def stop(self):
        """Stop the VAD engine."""
        self._running = False
        self._state = SpeechState.SILENCE
        self._silence_frames = 0
        self._chunk_buffer = np.array([], dtype=np.float32)
        logger.info("VAD engine stopped.")

    # ── Callbacks ────────────────────────────────────────────────

    def on_speech_start(self, callback: Callable):
        """Register callback for when speech begins."""
        self._on_speech_start = callback

    def on_speech_end(self, callback: Callable):
        """Register callback for when speech ends (silence detected)."""
        self._on_speech_end = callback

    def on_interrupt(self, callback: Callable):
        """Register callback for barge-in (user speaks while AI is speaking)."""
        self._on_interrupt = callback

    # ── Processing ───────────────────────────────────────────────

    def process_chunk(self, audio_data: np.ndarray) -> float:
        """
        Process one chunk of audio and return speech probability.
        Audio is accumulated internally; VAD runs when >= WINDOW_SIZE samples available.

        Args:
            audio_data: float32 numpy array, range [-1, 1], mono.

        Returns:
            Speech probability [0.0 - 1.0] (average across all windows processed,
            or 0.0 if not enough samples yet).
        """
        if self._vad is None:
            raise RuntimeError("VAD not started. Call start() first.")

        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Silero VAD Lite expects 1D float32 array
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)  # to mono

        # Accumulate into the internal buffer
        self._chunk_buffer = np.concatenate([self._chunk_buffer, audio_data])

        # Process all available full windows
        probabilities = []
        while len(self._chunk_buffer) >= self.WINDOW_SIZE:
            window = self._chunk_buffer[:self.WINDOW_SIZE]
            self._chunk_buffer = self._chunk_buffer[self.WINDOW_SIZE:]
            probabilities.append(self._vad.process(window))

        if probabilities:
            return float(np.mean(probabilities))
        # Not enough samples yet — return 0 (no speech)
        return 0.0

    def is_speech(self, probability: float) -> bool:
        """Check if probability exceeds threshold."""
        return probability >= self.threshold

    async def process_chunk_with_state(
        self,
        audio_data: np.ndarray,
        ai_is_speaking: bool = False,
    ) -> dict:
        """
        Process audio chunk and manage speech state machine.

        Args:
            audio_data: Audio chunk as float32 numpy array.
            ai_is_speaking: Whether the AI is currently speaking (for barge-in detection).

        Returns:
            Dict with 'probability', 'state', 'event' keys.
        """
        probability = self.process_chunk(audio_data)
        is_speech = self.is_speech(probability)
        event = None

        if is_speech:
            self._silence_frames = 0

            if self._state == SpeechState.SILENCE:
                # SILENCE → SPEECH transition
                self._state = SpeechState.SPEECH
                event = "speech_start"
                logger.debug(f"Speech detected (prob={probability:.2f})")

                if ai_is_speaking:
                    # Barge-in: user interrupted AI
                    event = "interrupt"
                    logger.info("Barge-in detected — user interrupted AI.")
                    await self._fire(self._on_interrupt)
                else:
                    await self._fire(self._on_speech_start)

        else:
            if self._state == SpeechState.SPEECH:
                self._silence_frames += len(audio_data)
                silence_ms = (self._silence_frames / self.sample_rate) * 1000

                if silence_ms >= self.silence_duration_ms:
                    # SPEECH → SILENCE transition
                    self._state = SpeechState.SILENCE
                    self._silence_frames = 0
                    event = "speech_end"
                    logger.debug(f"Speech ended after {silence_ms:.0f}ms silence.")
                    await self._fire(self._on_speech_end)

        return {
            "probability": probability,
            "state": self._state.value,
            "event": event,
        }

    # ── Utilities ────────────────────────────────────────────────

    @property
    def current_state(self) -> SpeechState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def bytes_to_float32(audio_bytes: bytes, sample_width: int = 2) -> np.ndarray:
        """
        Convert raw PCM bytes to float32 numpy array.

        Args:
            audio_bytes: Raw PCM audio bytes.
            sample_width: Bytes per sample (2 = 16-bit PCM).

        Returns:
            float32 numpy array in range [-1, 1].
        """
        if sample_width == 2:
            audio = np.frombuffer(audio_bytes, dtype=np.int16)
            return audio.astype(np.float32) / 32768.0
        elif sample_width == 4:
            audio = np.frombuffer(audio_bytes, dtype=np.int32)
            return audio.astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")

    async def _fire(self, callback: Optional[Callable]):
        """Fire a callback (sync or async)."""
        if callback is None:
            return
        if asyncio.iscoroutinefunction(callback):
            await callback()
        else:
            callback()
