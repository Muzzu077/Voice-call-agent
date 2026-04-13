"""
TTS Engine — streaming text-to-speech using Kokoro ONNX (primary) with sounddevice output.
Falls back gracefully if Kokoro unavailable.
"""

import asyncio
import io
import logging
import queue
import threading
from typing import AsyncGenerator, Callable, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Text-to-speech engine with streaming support.

    Primary: kokoro-onnx (lightweight, high-quality)
    Fallback: pyttsx3 or silent stub

    Usage:
        engine = TTTEngine()
        engine.start()
        await engine.speak("Hello, how can I help?")
        engine.stop()
    """

    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        self.voice = voice
        self.speed = speed
        self._backend: Optional[str] = None
        self._kokoro = None
        self._running = False
        self._stop_event = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
        self._audio_queue: queue.Queue = queue.Queue()

        # Interrupt flag: set by VAD barge-in
        self._interrupted = False

        # Callback fired when speech finishes
        self._on_complete: Optional[Callable] = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Initialize TTS backend."""
        self._backend = self._detect_backend()
        if self._backend == "kokoro":
            self._init_kokoro()
        self._running = True
        logger.info(f"TTS engine started (backend={self._backend}, voice={self.voice})")

    def stop(self):
        """Stop TTS and release resources."""
        self.interrupt()
        self._running = False
        self._kokoro = None
        logger.info("TTS engine stopped.")

    # ── Callbacks ────────────────────────────────────────────────

    def on_complete(self, callback: Callable):
        """Register callback called when speech finishes playing."""
        self._on_complete = callback

    # ── Core API ─────────────────────────────────────────────────

    async def speak(self, text: str):
        """
        Synthesize text and play it through the speaker.
        Blocks until playback is complete or interrupted.

        Args:
            text: Text to synthesize and speak.
        """
        if not text or not text.strip():
            return

        self._interrupted = False
        logger.debug(f"Speaking: '{text[:80]}...' " if len(text) > 80 else f"Speaking: '{text}'")

        if self._backend == "kokoro":
            await self._speak_kokoro(text)
        else:
            await self._speak_stub(text)

        if self._on_complete and not self._interrupted:
            if asyncio.iscoroutinefunction(self._on_complete):
                await self._on_complete()
            else:
                self._on_complete()

    async def synthesize(self, text: str) -> np.ndarray:
        """
        Synthesize text to audio array without playing.

        Returns:
            float32 numpy array of audio samples at 24kHz.
        """
        if self._backend == "kokoro" and self._kokoro:
            samples, sample_rate = self._kokoro.create(
                text, voice=self.voice, speed=self.speed, lang="en-us"
            )
            return samples.astype(np.float32), sample_rate

        # Stub: return 1 second of silence
        return np.zeros(24000, dtype=np.float32), 24000

    async def synthesize_stream(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """
        Synthesize text in chunks for lower latency streaming.
        Yields numpy audio arrays.
        """
        # Split text into sentences for lower TTFA (time-to-first-audio)
        sentences = self._split_sentences(text)

        for sentence in sentences:
            if self._interrupted:
                break
            if not sentence.strip():
                continue

            audio, sr = await self.synthesize(sentence)
            if audio is not None and len(audio) > 0:
                yield audio

    def interrupt(self):
        """
        Stop current speech immediately (barge-in support).
        Called when VAD detects the user speaking.
        """
        self._interrupted = True
        self._stop_event.set()
        logger.debug("TTS interrupted.")

    def is_speaking(self) -> bool:
        """Check if TTS is currently playing audio."""
        return self._running and not self._interrupted and self._playback_thread is not None and self._playback_thread.is_alive()

    # ── Internal: Kokoro ─────────────────────────────────────────

    def _init_kokoro(self):
        """Load the Kokoro ONNX model."""
        try:
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
            logger.info("Kokoro ONNX model loaded.")
        except FileNotFoundError:
            logger.warning("Kokoro model files not found. Run: python download_kokoro.py")
            self._backend = "stub"
        except Exception as e:
            logger.warning(f"Kokoro init failed: {e}. Using stub.")
            self._backend = "stub"

    async def _speak_kokoro(self, text: str):
        """Synthesize and play using Kokoro."""
        import sounddevice as sd

        try:
            sentences = self._split_sentences(text)
            for sentence in sentences:
                if self._interrupted:
                    break
                if not sentence.strip():
                    continue

                # Synthesize sentence
                samples, sample_rate = self._kokoro.create(
                    sentence, voice=self.voice, speed=self.speed, lang="en-us"
                )
                samples = samples.astype(np.float32)

                if self._interrupted:
                    break

                # Play with blocking (allows interrupt check)
                self._stop_event.clear()
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda s=samples, sr=sample_rate: self._play_with_interrupt(s, sr),
                )

        except Exception as e:
            logger.error(f"Kokoro speak error: {e}")

    def _play_with_interrupt(self, samples: np.ndarray, sample_rate: int):
        """Play audio in a thread, checking for interrupt."""
        try:
            import sounddevice as sd
            with sd.OutputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
                chunk_size = sample_rate // 10  # 100ms chunks
                for i in range(0, len(samples), chunk_size):
                    if self._interrupted:
                        stream.abort()
                        break
                    chunk = samples[i:i + chunk_size]
                    stream.write(chunk)
        except Exception as e:
            logger.warning(f"Audio playback error: {e}")

    async def _speak_stub(self, text: str):
        """Stub TTS: logs the text, simulates speaking delay."""
        words = len(text.split())
        duration = words * 0.3  # ~0.3s per word
        logger.info(f"[TTS STUB] Would speak ({duration:.1f}s): '{text[:100]}'")
        # Simulate speaking time with interrupt support
        step = 0.1
        elapsed = 0.0
        while elapsed < duration and not self._interrupted:
            await asyncio.sleep(step)
            elapsed += step

    # ── Internal: Utilities ──────────────────────────────────────

    @staticmethod
    def _detect_backend() -> str:
        """Detect available TTS backend."""
        try:
            import kokoro_onnx
            return "kokoro"
        except ImportError:
            pass
        logger.warning("No TTS backend found. Using stub (text only, no audio).")
        return "stub"

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences for streaming synthesis."""
        import re
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s for s in sentences if s.strip()]
