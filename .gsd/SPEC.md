1# SPEC.md — Project Specification

> **Status**: `FINALIZED`
>
> ⚠️ **Planning Lock**: No code may be written until this spec is marked
> `FINALIZED`.

## Vision

A production-grade, real-time autonomous AI voice agent that handles phone
calls, speaks naturally with low latency, executes actions via tool calling,
remembers context through vector memory, and validates all actions before
execution. This is NOT a chatbot — it is a conversational AI decision-making
system with telephony, memory, and action engines.

## Goals

1. **Real-Time Voice Conversation** — Sub-second latency voice interaction with
   streaming STT/TTS and barge-in support
2. **Intelligent Memory System** — Dual-layer memory (SQLite structured +
   ChromaDB semantic) with rolling summaries for context retrieval
3. **Action Execution Engine** — Tool calling via structured JSON output from
   LLM, with safety validation before execution
4. **Telephony Integration** — Handle inbound/outbound phone calls via Twilio
   with real-time audio streaming
5. **Production API Backend** — FastAPI-based async backend with WebSocket
   support for real-time audio streams

## Non-Goals (Out of Scope)

- Web/mobile frontend UI (API-only for Phase 1)
- Multi-tenant/multi-user support
- Custom voice cloning or voice model training
- Multi-language support (English-only initially)
- Asterisk PBX integration (Twilio only for MVP)
- Distributed deployment / Kubernetes orchestration

## Constraints

- **Local-first LLM**: Uses Ollama for LLM inference (no cloud LLM dependency)
- **GPU recommended**: Whisper STT and TTS benefit from GPU acceleration
- **Python 3.11+**: Required for async features and library compatibility
- **Windows primary**: Development on Windows, must be Linux-deployable
- **Open-source stack**: All core components must be open-source or have free
  tiers

## Success Criteria

- [ ] Voice conversation round-trip latency < 2 seconds (mic → response audio)
- [ ] Barge-in interruption stops TTS within 200ms
- [ ] Tool calls (reminders, tasks, notes) execute correctly > 90% of the time
- [ ] Memory retrieval returns relevant context from past conversations
- [ ] Twilio phone calls connect and stream audio bidirectionally
- [ ] System handles 10+ minute continuous conversations without memory leaks
- [ ] Rolling summary compresses conversation history after 10 messages

## User Stories

### As a caller

- I want to speak naturally and be understood in real-time
- So that the conversation feels like talking to a human assistant

### As a user giving commands

- I want to say "remind me to call John at 6 PM" and have it happen
- So that the AI acts on my behalf, not just responds

### As a returning user

- I want the AI to remember what we discussed yesterday
- So that I don't have to repeat context every session

### As a phone caller

- I want to call a number and interact with the AI agent
- So that I can use the system from any phone

## Technical Requirements

| Requirement                           | Priority     | Notes                                  |
| ------------------------------------- | ------------ | -------------------------------------- |
| Silero VAD for speech detection       | Must-have    | Real-time, CPU-efficient               |
| Faster-Whisper for STT                | Must-have    | Streaming chunk-based transcription    |
| Ollama for LLM (Llama 3.1+ or Qwen 3) | Must-have    | Local, streaming, tool-calling support |
| Kokoro TTS or Piper TTS               | Must-have    | Low-latency, open-source               |
| ChromaDB for vector memory            | Must-have    | Semantic search over conversations     |
| SQLite for structured data            | Must-have    | Tasks, reminders, call logs            |
| FastAPI + WebSockets                  | Must-have    | Async real-time backend                |
| Twilio for telephony                  | Should-have  | Phase 4 integration                    |
| Action validation layer               | Should-have  | Safety checks before execution         |
| Rolling summary engine                | Nice-to-have | Compress long conversations            |

---

_Last updated: 2026-04-13_
