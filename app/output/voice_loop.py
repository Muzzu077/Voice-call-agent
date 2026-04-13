"""
Real-Time Voice Loop — ties together the full pipeline:
  Mic → VAD → STT → Agent Brain → TTS → Speaker
  with barge-in support.

This is the COMPLETE real-time conversation loop for Phase 3.
"""

import asyncio
import logging
from typing import Optional

from app.input.audio_pipeline import AudioPipeline, PipelineState
from app.output.audio_output import AudioOutput
from app.output.tts_engine import TTSEngine
from app.brain.agent_service import AgentService

logger = logging.getLogger(__name__)


class VoiceLoop:
    """
    Full real-time voice conversation loop.

    Flow:
        Mic audio → VAD → Buffer → STT
                         ↓ (transcript)
                    Agent Brain (LLM + Memory + Tools)
                         ↓ (response text)
                    TTS Engine → Speaker
                         ↑
                    VAD barge-in → interrupt TTS
    """

    def __init__(self, agent: AgentService):
        self.agent = agent
        self.tts_engine = TTSEngine()
        self.audio_output = AudioOutput(self.tts_engine)
        self.pipeline = AudioPipeline()

        self._running = False
        self._loop_task: Optional[asyncio.Task] = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Initialize all components and start the voice loop."""
        # Start TTS output
        self.audio_output.start()

        # Wire barge-in: when VAD fires interrupt, stop TTS
        self.pipeline.on_interrupt(self._handle_barge_in)

        # Wire transcript: when STT produces text, run agent
        self.pipeline.on_transcript(self._handle_transcript)

        # Wire state changes to speaking flag
        self.audio_output.on_speaking_start(
            lambda: self.pipeline.set_ai_speaking(True)
        )
        self.audio_output.on_speaking_stop(
            lambda: self.pipeline.set_ai_speaking(False)
        )

        # Start audio input pipeline (downloads STT model if needed)
        self.pipeline.start()

        self._running = True
        logger.info("Voice loop started. Ready for real-time conversation.")

    def stop(self):
        """Stop all components."""
        self._running = False
        self.pipeline.stop()
        self.audio_output.stop()
        logger.info("Voice loop stopped.")

    # ── Event Handlers ───────────────────────────────────────────

    async def _handle_transcript(self, text: str, confidence: float):
        """Called when STT produces a transcription — process through agent."""
        if not text.strip():
            return

        logger.info(f"User said: '{text}' (conf={confidence:.2f})")

        try:
            # Process through agent brain
            result = await self.agent.process_message(text)
            response_text = result["response"]
            action_result = result.get("action_result")

            logger.info(f"Agent: '{response_text[:100]}...' " if len(response_text) > 100 else f"Agent: '{response_text}'")

            # Speak the response
            if response_text:
                await self.audio_output.speak(response_text)

            # If an action was taken, optionally speak the confirmation too
            if action_result and self.audio_output.is_speaking is False:
                logger.info(f"Action result: {action_result}")

        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            await self.audio_output.speak("Sorry, I encountered an error. Please try again.")

    async def _handle_barge_in(self):
        """Called when user speaks while AI is talking — stop TTS immediately."""
        logger.info("Barge-in: stopping TTS.")
        self.audio_output.interrupt()

    # ── Microphone Input ─────────────────────────────────────────

    async def run_from_mic(self):
        """
        Capture audio from microphone and process through the voice loop.
        Runs until stop() is called.

        Requires: sounddevice installed and a microphone available.
        """
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice not installed. Run: pip install sounddevice")
            return

        sample_rate = self.pipeline.vad.sample_rate
        chunk_duration = 0.032   # 32ms chunks (512 samples at 16kHz)
        chunk_samples = int(sample_rate * chunk_duration)

        logger.info(f"Starting microphone capture ({sample_rate}Hz, {chunk_samples} samples/chunk)...")

        loop = asyncio.get_event_loop()
        audio_queue: asyncio.Queue = asyncio.Queue()

        def mic_callback(indata, frames, time, status):
            """Sounddevice callback — runs in audio thread."""
            if status:
                logger.warning(f"Mic status: {status}")
            # Convert to float32 mono and enqueue
            audio_chunk = indata[:, 0].astype("float32")
            loop.call_soon_threadsafe(audio_queue.put_nowait, audio_chunk.tobytes())

        try:
            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_samples,
                callback=mic_callback,
            ):
                logger.info("Microphone active. Speak now...")
                while self._running:
                    try:
                        audio_bytes = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
                        await self.pipeline.process_chunk(audio_bytes, sample_width=4)  # float32 = 4 bytes
                    except asyncio.TimeoutError:
                        continue  # No audio, check running flag

        except Exception as e:
            logger.error(f"Microphone error: {e}")

    # ── Properties ───────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def pipeline_state(self) -> str:
        return self.pipeline.state.value
