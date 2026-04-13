"""
STT Engine — streaming speech-to-text using Faster-Whisper.
Supports chunk-based transcription with GPU/CPU fallback.
"""

import logging
from typing import Optional, Tuple

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class STTEngine:
    """
    Faster-Whisper based STT engine with streaming support.

    Usage pattern:
        engine.start()                          # load model once
        text = engine.transcribe(audio_array)   # transcribe buffered audio
        engine.stop()                           # release resources
    """

    def __init__(
        self,
        model_size: Optional[str] = None,
        device: str = "auto",
        language: str = "en",
    ):
        self.model_size = model_size or settings.WHISPER_MODEL_SIZE
        self.language = language
        self._model = None
        self._running = False

        # Determine compute device
        if device == "auto":
            self._device, self._compute_type = self._detect_device()
        else:
            self._device = device
            self._compute_type = "float16" if device == "cuda" else "int8"

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Load the Whisper model."""
        if self._model is not None:
            return  # already loaded

        from faster_whisper import WhisperModel

        logger.info(
            f"Loading Whisper '{self.model_size}' on {self._device} "
            f"(compute={self._compute_type})..."
        )
        self._model = WhisperModel(
            self.model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        self._running = True
        logger.info(f"STT engine ready.")

    def stop(self):
        """Release the model (frees GPU/CPU memory)."""
        self._model = None
        self._running = False
        logger.info("STT engine stopped.")

    # ── Transcription ────────────────────────────────────────────

    def transcribe(self, audio: np.ndarray) -> Tuple[str, float]:
        """
        Transcribe a complete audio buffer to text.

        Args:
            audio: float32 numpy array at 16kHz, mono, range [-1, 1].

        Returns:
            Tuple of (transcription_text, avg_confidence).
        """
        if self._model is None:
            raise RuntimeError("STT not started. Call start() first.")

        if len(audio) == 0:
            return "", 0.0

        # Whisper requires float32 16kHz mono
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        try:
            segments, info = self._model.transcribe(
                audio,
                language=self.language,
                beam_size=5,
                vad_filter=False,   # We have our own VAD
                condition_on_previous_text=False,
            )

            # Collect all segments
            text_parts = []
            confidences = []
            for segment in segments:
                text_parts.append(segment.text.strip())
                # avg_logprob is negative; convert to 0-1 scale approx
                if hasattr(segment, "avg_logprob"):
                    conf = min(1.0, max(0.0, 1.0 + segment.avg_logprob / 5.0))
                    confidences.append(conf)

            full_text = " ".join(text_parts).strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else 1.0

            logger.debug(f"Transcribed: '{full_text}' (conf={avg_conf:.2f})")
            return full_text, avg_conf

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "", 0.0

    def transcribe_bytes(self, audio_bytes: bytes, sample_width: int = 2) -> Tuple[str, float]:
        """
        Transcribe raw PCM bytes.

        Args:
            audio_bytes: Raw 16-bit PCM bytes at 16kHz.
            sample_width: Bytes per sample (default 2 = 16-bit).

        Returns:
            Tuple of (transcription_text, confidence).
        """
        if not audio_bytes:
            return "", 0.0

        # Convert bytes → float32 numpy
        if sample_width == 2:
            pcm = np.frombuffer(audio_bytes, dtype=np.int16)
            audio = pcm.astype(np.float32) / 32768.0
        else:
            raise ValueError(f"Unsupported sample_width: {sample_width}")

        return self.transcribe(audio)

    # ── Getters ──────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._model is not None and self._running

    @property
    def device(self) -> str:
        return self._device

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _detect_device() -> Tuple[str, str]:
        """
        Auto-detect best available compute device.

        Returns:
            Tuple of (device, compute_type).
        """
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("CUDA GPU detected — using float16.")
                return "cuda", "float16"
        except ImportError:
            pass

        logger.info("No GPU detected — using CPU with int8 quantization.")
        return "cpu", "int8"
