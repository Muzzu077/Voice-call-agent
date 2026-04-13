---
milestone: MVP Voice Agent
version: 0.1.0
updated: 2026-04-13
---

# Roadmap

> **Current Phase:** 5 - Summarization & Safety Validation
> **Status:** planning

## Must-Haves (from SPEC)

- [ ] Voice conversation with < 2s round-trip latency
- [ ] Barge-in interruption within 200ms
- [ ] Tool calls execute correctly > 90%
- [ ] Memory retrieval returns relevant context
- [ ] Twilio phone call integration
- [ ] Rolling summary compression

---

## Phases

### Phase 1: Foundation — LLM + Memory + Tool Calling
**Status:** ⬜ Not Started
**Objective:** Core brain working: Ollama LLM with streaming, ChromaDB memory, SQLite storage, tool calling via JSON parsing. Text-only (no audio yet).
**Requirements:** REQ-01 (LLM), REQ-02 (Memory), REQ-03 (Tool Calling)

**Deliverables:**
- Working Ollama streaming chat
- ChromaDB storing/retrieving conversation embeddings
- SQLite with tasks, reminders, call_logs tables
- JSON tool-call detection and action dispatch
- FastAPI /chat endpoint (text-only)

**Plans:**
- [x] Plan 1.1: Project scaffolding + config + database setup
- [x] Plan 1.2: Ollama LLM engine + context builder + tool parser
- [x] Plan 1.3: Memory service (ChromaDB + SQLite) + action execution

---

### Phase 2: Audio Pipeline — VAD + Streaming STT
**Status:** ⬜ Not Started
**Objective:** Real-time audio input with voice activity detection and streaming speech-to-text.
**Depends on:** Phase 1

**Deliverables:**
- Silero VAD detecting speech start/stop
- Faster-Whisper transcribing audio chunks
- Audio buffer management
- WebSocket /stream-audio endpoint

**Plans:**
- [x] Plan 2.1: VAD engine + audio buffer
- [x] Plan 2.2: Streaming STT + WebSocket integration

---

### Phase 3: Voice Output — TTS + Real-Time Loop
**Status:** ⬜ Not Started
**Objective:** Complete real-time voice loop: speak → hear → process → respond → speak. With barge-in support.
**Depends on:** Phase 2

**Deliverables:**
- Streaming TTS (Kokoro/Piper)
- Full real-time conversation loop
- Barge-in: VAD triggers TTS stop
- Audio output management

**Plans:**
- [ ] Plan 3.1: TTS engine + audio output
- [ ] Plan 3.2: Real-time loop integration + barge-in

---

### Phase 4: Telephony — Twilio Call Integration
**Status:** ⬜ Not Started
**Objective:** Handle inbound/outbound phone calls with the AI agent.
**Depends on:** Phase 3

**Deliverables:**
- Twilio webhook endpoints
- Bidirectional audio streaming over phone
- Call transcript storage
- Post-call summarization

**Plans:**
- [ ] Plan 4.1: Twilio webhooks + audio streaming
- [ ] Plan 4.2: Call transcript + summary + task extraction

---

### Phase 5: Intelligence — Summarization + Validation
**Status:** ⬜ Not Started
**Objective:** Add safety validation layer and rolling memory compression.
**Depends on:** Phase 3

**Deliverables:**
- Action validation (safety checks, boundary enforcement)
- Rolling summary engine (10 messages → compress)
- Intent confirmation for risky actions
- Production hardening

**Plans:**
- [ ] Plan 5.1: Action validation layer
- [ ] Plan 5.2: Rolling summary engine + memory optimization

---

## Progress Summary

| Phase | Status | Plans | Complete |
|-------|--------|-------|----------|
| 1 | ⬜ | 0/3 | — |
| 2 | ⬜ | 0/2 | — |
| 3 | ⬜ | 0/2 | — |
| 4 | ⬜ | 0/2 | — |
| 5 | ⬜ | 0/2 | — |

---

## Timeline

| Phase | Started | Completed | Duration |
|-------|---------|-----------|----------|
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |
| 4 | — | — | — |
| 5 | — | — | — |
