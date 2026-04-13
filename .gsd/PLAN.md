# Phase 2 Plan: Audio Pipeline — VAD + Streaming STT

> **Phase:** 2
> **Status:** Ready
> **Objective:** Real-time audio input with voice activity detection (Silero VAD) and streaming speech-to-text (Faster-Whisper). WebSocket endpoint for audio streaming.

---

## Wave 1 — VAD Engine + Audio Buffer

<task type="auto" effort="high">
  <name>Create Silero VAD engine for real-time speech detection</name>
  <files>app/input/vad_engine.py</files>
  <action>
    Real-time voice activity detection using silero-vad-lite.
    - VADEngine class with start()/stop() lifecycle
    - process_chunk(audio_data): returns speech probability float
    - is_speaking(probability): threshold comparison
    - on_speech_start callback: trigger STT
    - on_speech_end callback: finalize STT segment
    - on_interrupt callback: stop TTS playback (barge-in)
    - Configurable threshold from settings.VAD_THRESHOLD
    - Works with 16kHz mono audio, 512-sample frames
    - Track speech state transitions (silence→speech, speech→silence)
  </action>
  <verify>python -c "from app.input.vad_engine import VADEngine; v = VADEngine(); print('VAD OK')"</verify>
  <done>VAD engine detects speech start/end, barge-in interrupts, configurable threshold</done>
</task>

<task type="auto" effort="medium">
  <name>Create audio buffer for chunk management</name>
  <files>app/input/audio_buffer.py</files>
  <action>
    Manages audio chunk buffering for STT pipeline.
    - AudioBuffer class
    - add_chunk(data): append audio bytes
    - get_buffer(): return accumulated audio
    - clear(): reset buffer
    - get_duration(): return buffer duration in seconds
    - Thread-safe with asyncio.Lock
    - Configurable chunk size (default 0.5s at 16kHz = 8000 samples)
    - Support for converting between bytes/numpy arrays
  </action>
  <verify>python -c "from app.input.audio_buffer import AudioBuffer; b = AudioBuffer(); print('Buffer OK')"</verify>
  <done>Audio buffer manages chunks, thread-safe, converts formats</done>
</task>

---

## Wave 2 — Streaming STT + WebSocket Integration

<task type="auto" effort="high">
  <name>Create Faster-Whisper streaming STT engine</name>
  <files>app/input/stt_engine.py</files>
  <action>
    Streaming speech-to-text using faster-whisper.
    - STTEngine class with start()/stop() lifecycle
    - transcribe_chunk(audio_data): process audio chunk, return partial text
    - transcribe_buffer(audio_buffer): process full buffer, return final text
    - Stream mode: accumulate chunks, transcribe when VAD signals speech end
    - Configurable model size from settings (tiny/base/small/medium)
    - GPU acceleration if available, CPU fallback
    - Return both partial and final transcriptions
    - Handle audio format conversion (bytes → float32 numpy)
  </action>
  <verify>python -c "from app.input.stt_engine import STTEngine; e = STTEngine(); print('STT OK')"</verify>
  <done>STT engine transcribes audio chunks, supports streaming, GPU/CPU modes</done>
</task>

<task type="auto" effort="high">
  <name>Create audio pipeline orchestrator</name>
  <files>app/input/audio_pipeline.py</files>
  <action>
    Orchestrates VAD → Buffer → STT pipeline.
    - AudioPipeline class
    - process_audio(chunk): full pipeline
      1. VAD checks for speech
      2. If speaking: buffer audio
      3. On speech end: send buffer to STT
      4. Return transcription result
    - Callbacks for: transcript_ready, interrupt_detected
    - Manages state machine: IDLE → LISTENING → PROCESSING
    - Async processing with asyncio
  </action>
  <verify>python -c "from app.input.audio_pipeline import AudioPipeline; p = AudioPipeline(); print('Pipeline OK')"</verify>
  <done>Audio pipeline orchestrates VAD→Buffer→STT, state machine works</done>
</task>

<task type="auto" effort="high">
  <name>Create WebSocket audio streaming endpoint</name>
  <files>app/api/routes/audio.py</files>
  <action>
    WebSocket endpoint for real-time audio streaming.
    - WS /ws/audio: bidirectional audio stream
    - Receives: raw audio bytes from client (16kHz, mono, 16-bit PCM)
    - Processes through audio pipeline (VAD → STT)
    - Sends transcription to agent brain
    - Returns: AI response text (for TTS in Phase 3)
    - Handle connection lifecycle (connect/disconnect)
    - Handle barge-in (interrupt signal)
    - Error handling and graceful disconnection
    - Register route in main.py
  </action>
  <verify>Start server and verify WebSocket endpoint is accessible at ws://localhost:8000/ws/audio</verify>
  <done>WebSocket accepts audio, processes through pipeline, returns AI text responses</done>
</task>

---

## Verification Checklist

- [ ] Silero VAD detects speech start/end from audio data
- [ ] Audio buffer manages chunks correctly
- [ ] Faster-Whisper transcribes audio to text
- [ ] Audio pipeline orchestrates VAD→STT flow
- [ ] WebSocket endpoint accepts audio and returns text
- [ ] Barge-in detection triggers interrupt callback
