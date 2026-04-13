"""
Audio Buffer — thread-safe accumulation of audio chunks for STT processing.
"""

import asyncio
import logging
from typing import Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class AudioBuffer:
    """
    Async-safe audio buffer that accumulates chunks between speech events.

    Usage:
        buf = AudioBuffer()
        buf.add_chunk(np.array([...]))   # from VAD
        audio = buf.get_buffer()          # pass to STT
        buf.clear()                       # after STT
    """

    def __init__(self, sample_rate: int = None):
        self.sample_rate = sample_rate or settings.AUDIO_SAMPLE_RATE
        self._buffer: list[np.ndarray] = []
        self._lock = asyncio.Lock()

    # ── Write ────────────────────────────────────────────────────

    async def add_chunk(self, chunk: np.ndarray):
        """Append a float32 audio chunk to the buffer."""
        async with self._lock:
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32)
            self._buffer.append(chunk)

    def add_chunk_sync(self, chunk: np.ndarray):
        """Synchronous add (for use in non-async contexts)."""
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)
        self._buffer.append(chunk)

    # ── Read ─────────────────────────────────────────────────────

    async def get_buffer(self) -> np.ndarray:
        """Return accumulated audio as a single float32 array."""
        async with self._lock:
            if not self._buffer:
                return np.array([], dtype=np.float32)
            return np.concatenate(self._buffer)

    def get_buffer_sync(self) -> np.ndarray:
        """Synchronous get (for non-async contexts)."""
        if not self._buffer:
            return np.array([], dtype=np.float32)
        return np.concatenate(self._buffer)

    # ── State ────────────────────────────────────────────────────

    async def clear(self):
        """Clear all buffered audio."""
        async with self._lock:
            self._buffer.clear()

    def clear_sync(self):
        """Synchronous clear."""
        self._buffer.clear()

    async def get_duration(self) -> float:
        """Return buffer duration in seconds."""
        async with self._lock:
            total_samples = sum(len(c) for c in self._buffer)
            return total_samples / self.sample_rate

    async def is_empty(self) -> bool:
        """Check if buffer has no audio."""
        async with self._lock:
            return len(self._buffer) == 0

    async def get_sample_count(self) -> int:
        """Return total number of samples in buffer."""
        async with self._lock:
            return sum(len(c) for c in self._buffer)

    # ── Conversions ──────────────────────────────────────────────

    @staticmethod
    def bytes_to_float32(raw_bytes: bytes, sample_width: int = 2) -> np.ndarray:
        """Convert raw PCM bytes to float32 numpy array in range [-1, 1]."""
        if sample_width == 2:
            pcm = np.frombuffer(raw_bytes, dtype=np.int16)
            return pcm.astype(np.float32) / 32768.0
        raise ValueError(f"Unsupported sample_width: {sample_width}. Use 2 (16-bit).")

    @staticmethod
    def float32_to_bytes(audio: np.ndarray) -> bytes:
        """Convert float32 numpy array back to 16-bit PCM bytes."""
        clipped = np.clip(audio, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes()

    def __repr__(self):
        total = sum(len(c) for c in self._buffer)
        duration = total / self.sample_rate if self.sample_rate else 0
        return f"AudioBuffer(chunks={len(self._buffer)}, samples={total}, duration={duration:.2f}s)"
