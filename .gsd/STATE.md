---
updated: 2026-04-13
---

# Project State

## Current Position

**Milestone:** MVP Voice Agent
**Phase:** 5 - Summarization & Safety Validation
**Status:** planning

## Last Action

Phase 4 (Telephony) completed and verified via `verify_phase4.py`:
- `audio_utils.py`: Built-in format resamplers (8kHz mu-law <-> 16kHz/24kHz float32).
- `twilio.py`: Express `/call/incoming` webhook routing inbound calls to Media Streams WebSocket.
- `twilio_ws.py`: High-speed Twilio Media Streams handler with full duplex chunk transcoding.
- `audio_output.py`: Extended TTS bridging with `.stream()` buffer implementation for Media Streams.
- `main.py`: Full wiring and endpoint inclusion.

## Next Steps

1. Configure ngrok/tunnel for Twilio webhook to hit `localhost:8000`.
2. Physically call the assigned Twilio number `+1 641 693 6778` and perform a live conversation test.
3. Switch to Phase 5 completion (Pre-action verification pipeline & call summary storage).

## Phases Done

| Phase | Status | Commit |
|-------|--------|--------|
| 1 — Foundation | DONE | feat(phase-1-2) |
| 2 — Audio Pipeline | DONE | feat(phase-1-2) |
| 3 — Voice Output | DONE | feat(phase-3) |
| 4 — Telephony | DONE | feat(phase-4) |
| 5 — Summarization...| TODO | — |

## Active Decisions

| Decision | Choice | Made | Affects |
|----------|--------|------|---------|
| LLM Provider | Ollama (local) | 2026-04-13 | All phases |
| VAD Engine | Silero VAD Lite 0.2.1 | 2026-04-13 | Phase 2+ |
| STT Engine | faster-whisper 1.2.1 (CPU int8) | 2026-04-13 | Phase 2+ |
| TTS Engine | kokoro-onnx 1.0 (stub fallback) | 2026-04-13 | Phase 3+ |
| Vector DB | ChromaDB | 2026-04-13 | Phase 1+ |
| Structured DB | SQLite (aiosqlite) | 2026-04-13 | Phase 1+ |
| API Framework | FastAPI + WebSockets | 2026-04-13 | All phases |
| Telephony | Twilio (Webhooks + Media Stream) | 2026-04-13 | Phase 4+ |

## Blockers

- Real network test requires ngrok listening on `8000`.
- User must paste the Ngrok `/call/incoming` url into the Twilio Voice Webhook console.
