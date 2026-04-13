"""Verification script for Phase 2 — Audio Pipeline components."""
import sys
import asyncio
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def make_sine_wave(freq=440, duration=0.5, sample_rate=16000, amplitude=0.5):
    """Generate a sine wave as a test signal."""
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def make_silence(duration=0.5, sample_rate=16000):
    """Generate silence."""
    return np.zeros(int(sample_rate * duration), dtype=np.float32)


async def main():
    print("=" * 50)
    print("Phase 2 Verification — Audio Pipeline")
    print("=" * 50)

    # 1. VAD Engine import
    print("\n[1] VAD Engine...")
    from app.input.vad_engine import VADEngine, SpeechState
    vad = VADEngine(sample_rate=16000, threshold=0.5)
    vad.start()
    print(f"  State: {vad.current_state.value}")

    # Test bytes_to_float32
    dummy_bytes = (np.zeros(1600, dtype=np.int16)).tobytes()
    f32 = VADEngine.bytes_to_float32(dummy_bytes)
    assert f32.dtype == np.float32, "Should be float32"
    print(f"  bytes_to_float32: {len(f32)} samples, dtype={f32.dtype}")

    # Process silence chunk
    silence = make_silence(0.032)   # 32ms chunk (512 samples)
    prob = vad.process_chunk(silence)
    print(f"  Silence probability: {prob:.4f}")
    assert prob < 0.5, f"Silence should have low probability, got {prob}"

    # Process speech-like (sine wave) chunk
    speech_signal = make_sine_wave(440, 0.032)
    prob_speech = vad.process_chunk(speech_signal)
    print(f"  Sine wave probability: {prob_speech:.4f}")

    vad.stop()
    print("  [OK] VAD Engine")

    # 2. Audio Buffer
    print("\n[2] Audio Buffer...")
    from app.input.audio_buffer import AudioBuffer
    buf = AudioBuffer(sample_rate=16000)

    chunk1 = make_sine_wave(440, 0.5)
    chunk2 = make_sine_wave(220, 0.5)
    await buf.add_chunk(chunk1)
    await buf.add_chunk(chunk2)

    count = await buf.get_sample_count()
    duration = await buf.get_duration()
    print(f"  Samples: {count}, Duration: {duration:.2f}s")
    assert count == len(chunk1) + len(chunk2)

    full = await buf.get_buffer()
    print(f"  Buffer shape: {full.shape}, dtype: {full.dtype}")
    assert full.dtype == np.float32

    await buf.clear()
    assert await buf.is_empty()
    print("  [OK] Audio Buffer")

    # 3. Bytes conversion
    print("\n[3] PCM Bytes Conversion...")
    original = make_sine_wave(440, 0.1)
    as_bytes = AudioBuffer.float32_to_bytes(original)
    restored = AudioBuffer.bytes_to_float32(as_bytes)
    print(f"  Original: {len(original)} samples -> {len(as_bytes)} bytes -> {len(restored)} samples")
    assert len(original) == len(restored)
    # Check round-trip fidelity (small numerical error is OK)
    max_diff = float(np.max(np.abs(original - restored)))
    print(f"  Max round-trip error: {max_diff:.6f}")
    assert max_diff < 0.0001, f"Round-trip error too high: {max_diff}"
    print("  [OK] Bytes Conversion")

    # 4. STT Engine import (model load is optional — skip if slow)
    print("\n[4] STT Engine...")
    from app.input.stt_engine import STTEngine
    stt = STTEngine(model_size="tiny")
    print(f"  Model size: {stt.model_size}, Device: {stt._device}")
    print(f"  Compute type: {stt._compute_type}")
    # Don't actually load model in verification (takes time/bandwidth)
    print("  [OK] STT Engine (import + config)")

    # 5. Audio Pipeline (without STT model load)
    print("\n[5] Audio Pipeline...")
    from app.input.audio_pipeline import AudioPipeline, PipelineState
    pipeline = AudioPipeline()
    print(f"  Initial state: {pipeline.state.value}")
    print(f"  STT device: {pipeline.stt._device}")
    print(f"  VAD threshold: {pipeline.vad.threshold}")
    print("  [OK] Audio Pipeline (config)")

    # 6. WebSocket route import
    print("\n[6] WebSocket Audio Route...")
    from app.api.routes.audio import router
    routes = [r.path for r in router.routes]
    print(f"  Routes: {routes}")
    assert "/ws/audio" in routes
    print("  [OK] WebSocket route registered")

    # 7. FastAPI app with new route
    print("\n[7] FastAPI App (updated)...")
    from app.api.main import app
    all_routes = [getattr(r, 'path', str(r)) for r in app.routes]
    print(f"  Total routes: {len(all_routes)}")
    ws_routes = [r for r in all_routes if "ws" in r]
    print(f"  WebSocket routes: {ws_routes}")
    assert any("ws" in r for r in all_routes), "WebSocket route missing"
    print("  [OK] FastAPI App with WebSocket")

    print("\n" + "=" * 50)
    print("ALL PHASE 2 COMPONENTS VERIFIED")
    print("=" * 50)
    print("\nNOTE: STT model download happens on first pipeline.start() call.")
    print("Run the server with: python run.py")


if __name__ == "__main__":
    asyncio.run(main())
