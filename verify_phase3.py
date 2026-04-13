"""Verification script for Phase 3 — TTS + Real-Time Loop."""
import sys
import asyncio

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    print("=" * 50)
    print("Phase 3 Verification - TTS + Voice Loop")
    print("=" * 50)

    # 1. TTS Engine
    print("\n[1] TTS Engine...")
    from app.output.tts_engine import TTSEngine
    tts = TTSEngine(voice="af_heart", speed=1.0)
    backend = TTSEngine._detect_backend()
    print(f"  Detected backend: {backend}")
    print(f"  Voice: {tts.voice}, Speed: {tts.speed}")
    tts.start()
    print(f"  Backend active: {tts._backend}")
    assert tts._running
    assert tts._backend in ("kokoro", "stub")

    # Test sentence splitter
    sentences = TTSEngine._split_sentences("Hello world. How are you? I am fine!")
    print(f"  Sentence split: {sentences}")
    assert len(sentences) == 3

    # Test interrupt flag
    tts.interrupt()
    assert tts._interrupted
    tts._interrupted = False  # reset

    tts.stop()
    print("  [OK] TTS Engine")

    # 2. Audio Output
    print("\n[2] Audio Output...")
    from app.output.audio_output import AudioOutput
    tts2 = TTSEngine()
    tts2.start()
    ao = AudioOutput(tts2)
    ao.start()
    print(f"  is_speaking: {ao.is_speaking}")
    assert not ao.is_speaking

    # Test interrupt (should not raise even if not playing)
    ao.interrupt()

    # Test stub speak (no actual audio playback in test)
    if tts2._backend == "stub":
        await ao.speak("Testing the audio output system.")
    else:
        print("  Skipping actual playback (Kokoro needs model files)")

    ao.stop()
    print("  [OK] Audio Output")

    # 3. Voice Loop
    print("\n[3] Voice Loop...")
    from app.output.voice_loop import VoiceLoop
    from app.brain.agent_service import AgentService

    # Create minimal agent (don't initialize fully — no Ollama needed)
    agent = AgentService()
    loop = VoiceLoop(agent)
    print(f"  pipeline_state before start: {loop.pipeline.state.value}")
    print(f"  tts backend: {loop.tts_engine._backend}")
    # Don't call loop.start() — would download STT model
    print(f"  is_running: {loop.is_running}")
    print(f"  [OK] Voice Loop (config)")

    # 4. Updated FastAPI App
    print("\n[4] FastAPI App (Phase 3)...")
    from app.api.main import app, tts, audio_out
    routes = [getattr(r, 'path', str(r)) for r in app.routes]
    print(f"  Total routes: {len(routes)}")
    print(f"  TTS backend: {tts._backend}")
    assert len(routes) >= 15
    print(f"  [OK] FastAPI App")

    # 5. Audio route has set_audio_output
    print("\n[5] Audio Route injection...")
    from app.api.routes import audio as audio_route
    assert hasattr(audio_route, 'set_audio_output')
    print("  [OK] set_audio_output registered")

    print("\n" + "=" * 50)
    print("ALL PHASE 3 COMPONENTS VERIFIED")
    print("=" * 50)
    if tts._backend == "stub":
        print("\nNOTE: Kokoro model files not downloaded yet.")
        print("To download: python -m kokoro_onnx download")
        print("OR the stub will be used (TTS text-only, no audio).")
    else:
        print("\nKokoro TTS ready. Model files found.")


if __name__ == "__main__":
    asyncio.run(main())
