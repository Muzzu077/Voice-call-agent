"""
Audio Pipeline — orchestrates VAD → Buffer → STT in a real-time async loop.
"""

import asyncio
import logging
from enum import Enum
from typing import Callable, Optional

import numpy as np

from app.input.vad_engine import VADEngine, SpeechState
from app.input.audio_buffer import AudioBuffer
from app.input.stt_engine import STTEngine
from app.config import settings

logger = logging.getLogger(__name__)


class PipelineState(Enum):
    IDLE = "idle"
    LISTENING = "listening"      # VAD active, waiting for speech
    BUFFERING = "buffering"      # Speech detected, accumulating audio
    PROCESSING = "processing"    # STT transcribing, waiting for response
    INTERRUPTED = "interrupted"  # Barge-in detected


class AudioPipeline:
    """
    Real-time audio pipeline: VAD → Buffer → STT → Agent.

    Flow:
        chunk_in → VAD.process_chunk_with_state()
            ├─ speech_start  → start buffering
            ├─ (buffering)   → add_chunk to AudioBuffer
            ├─ speech_end    → STT.transcribe(buffer) → on_transcript callback
            └─ interrupt     → on_interrupt callback (stop TTS)
    """

    def __init__(self):
        self.vad = VADEngine()
        self.buffer = AudioBuffer()
        self.stt = STTEngine()
        self._state = PipelineState.IDLE
        self._ai_is_speaking = False

        # Callbacks
        self._on_transcript: Optional[Callable] = None
        self._on_interrupt: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start all pipeline components."""
        logger.info("Starting audio pipeline...")
        self.stt.start()
        self.vad.start()

        # Wire VAD callbacks
        self.vad.on_speech_start(self._handle_speech_start)
        self.vad.on_speech_end(self._handle_speech_end)
        self.vad.on_interrupt(self._handle_interrupt)

        self._state = PipelineState.LISTENING
        logger.info(f"Audio pipeline ready (device={self.stt.device}, "
                    f"model={self.stt.model_size}).")

    def stop(self):
        """Stop all pipeline components."""
        self.vad.stop()
        self.stt.stop()
        self._state = PipelineState.IDLE
        logger.info("Audio pipeline stopped.")

    # ── Callbacks ────────────────────────────────────────────────

    def on_transcript(self, callback: Callable):
        """Register callback called with (text: str) when speech is transcribed."""
        self._on_transcript = callback

    def on_interrupt(self, callback: Callable):
        """Register callback called when barge-in is detected."""
        self._on_interrupt = callback

    def on_state_change(self, callback: Callable):
        """Register callback called with (state: str) on state changes."""
        self._on_state_change = callback

    # ── Main Entry Point ─────────────────────────────────────────

    async def process_chunk(self, audio_bytes: bytes, sample_width: int = 2) -> dict:
        """
        Process one chunk of raw PCM audio through the full pipeline.

        Args:
            audio_bytes: Raw 16-bit PCM audio bytes at 16kHz mono.
            sample_width: Bytes per sample (2 = 16-bit).

        Returns:
            Dict with 'state', 'event', 'probability'.
        """
        # Convert bytes → float32
        audio_f32 = AudioBuffer.bytes_to_float32(audio_bytes, sample_width)

        # Run through VAD state machine
        result = await self.vad.process_chunk_with_state(
            audio_f32,
            ai_is_speaking=self._ai_is_speaking,
        )

        event = result.get("event")

        # If actively buffering (speech in progress), accumulate audio
        if self._state == PipelineState.BUFFERING and event != "speech_end":
            await self.buffer.add_chunk(audio_f32)

        return {
            "state": self._state.value,
            "event": event,
            "probability": result["probability"],
        }

    async def process_numpy_chunk(self, audio_f32: np.ndarray) -> dict:
        """
        Process one chunk of float32 audio (already converted).

        Args:
            audio_f32: float32 numpy array, 16kHz mono, range [-1, 1].
        """
        result = await self.vad.process_chunk_with_state(
            audio_f32,
            ai_is_speaking=self._ai_is_speaking,
        )
        event = result.get("event")

        if self._state == PipelineState.BUFFERING and event != "speech_end":
            await self.buffer.add_chunk(audio_f32)

        return {
            "state": self._state.value,
            "event": event,
            "probability": result["probability"],
        }

    # ── State Setters ────────────────────────────────────────────

    def set_ai_speaking(self, speaking: bool):
        """Tell pipeline whether AI is currently producing audio output."""
        self._ai_is_speaking = speaking

    # ── VAD Event Handlers ───────────────────────────────────────

    async def _handle_speech_start(self):
        """Speech detected — start buffering audio."""
        self._state = PipelineState.BUFFERING
        await self.buffer.clear()
        logger.debug("Pipeline: LISTENING → BUFFERING")
        await self._fire_state_change()

    async def _handle_speech_end(self):
        """Silence after speech — run STT on buffered audio."""
        if self._state != PipelineState.BUFFERING:
            return

        self._state = PipelineState.PROCESSING
        logger.debug("Pipeline: BUFFERING → PROCESSING")
        await self._fire_state_change()

        # Get accumulated audio
        audio = await self.buffer.get_buffer()
        await self.buffer.clear()

        duration = len(audio) / self.vad.sample_rate
        if duration < 0.2:
            logger.debug(f"Audio too short ({duration:.2f}s), skipping STT.")
            self._state = PipelineState.LISTENING
            await self._fire_state_change()
            return

        # Transcribe
        text, confidence = self.stt.transcribe(audio)

        self._state = PipelineState.LISTENING
        await self._fire_state_change()

        if text and self._on_transcript:
            logger.info(f"Transcript: '{text}' (conf={confidence:.2f})")
            if asyncio.iscoroutinefunction(self._on_transcript):
                await self._on_transcript(text, confidence)
            else:
                self._on_transcript(text, confidence)

    async def _handle_interrupt(self):
        """Barge-in: user spoke while AI was speaking."""
        self._state = PipelineState.BUFFERING
        await self.buffer.clear()
        logger.info("Pipeline: barge-in interrupt.")

        if self._on_interrupt:
            if asyncio.iscoroutinefunction(self._on_interrupt):
                await self._on_interrupt()
            else:
                self._on_interrupt()

        await self._fire_state_change()

    async def _fire_state_change(self):
        if self._on_state_change:
            if asyncio.iscoroutinefunction(self._on_state_change):
                await self._on_state_change(self._state.value)
            else:
                self._on_state_change(self._state.value)

    # ── Properties ───────────────────────────────────────────────

    @property
    def state(self) -> PipelineState:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._state != PipelineState.IDLE
