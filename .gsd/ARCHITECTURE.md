# Architecture

> Generated on 2026-04-13

## Overview

Real-time autonomous voice AI agent with 6 layered components: Input (VAD+STT), Brain (Context+LLM+Tools), Validation, Execution, Output (TTS), and Memory.

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT LAYER                                  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ Mic/Phone│───▶│  Silero VAD  │───▶│  Faster-Whisper STT  │   │
│  └──────────┘    └──────┬───────┘    └──────────┬───────────┘   │
│                         │ interrupt              │ transcript    │
└─────────────────────────┼────────────────────────┼──────────────┘
                          │                        │
                          ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT BRAIN                                  │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Context Builder  │─▶│  Ollama LLM  │─▶│  Tool Parser    │   │
│  │  - Vector recall  │  │  (streaming)  │  │  (JSON detect)  │   │
│  │  - Short-term mem │  └──────────────┘  └────────┬────────┘   │
│  │  - Personality    │                              │            │
│  └──────────────────┘                              │            │
└─────────────────────────────────────────────────────┼────────────┘
                                                      │
                          ┌───────────────────────────┤
                          ▼                           ▼
┌──────────────────────────────┐  ┌───────────────────────────────┐
│    VALIDATION LAYER          │  │       OUTPUT LAYER             │
│  - Safety check              │  │  ┌──────────┐  ┌──────────┐  │
│  - Intent confirmation       │  │  │  TTS     │─▶│ Speaker/ │  │
│  - Boundary enforcement      │  │  │ (stream) │  │  Phone   │  │
└──────────────┬───────────────┘  │  └──────────┘  └──────────┘  │
               │                  └───────────────────────────────┘
               ▼
┌──────────────────────────────┐
│    EXECUTION LAYER           │
│  ┌──────────┐ ┌───────────┐ │
│  │ Reminder │ │   Task    │ │
│  │  Engine  │ │  Engine   │ │
│  └──────────┘ └───────────┘ │
│  ┌──────────┐               │
│  │  Call     │               │
│  │  Engine   │               │
│  └──────────┘               │
└──────────────┬───────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MEMORY LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   SQLite      │  │  ChromaDB    │  │ Rolling Summaries  │    │
│  │  (structured) │  │  (semantic)  │  │  (compressor)      │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Input Layer
- **Purpose:** Capture audio, detect speech boundaries, transcribe in real-time
- **Location:** `app/input/`
- **Pattern:** Streaming pipeline with VAD gating

| File | Purpose | Priority |
|------|---------|----------|
| vad_engine.py | Silero VAD speech detection + interrupt detection | High |
| stt_engine.py | Faster-Whisper streaming transcription | High |
| audio_buffer.py | Chunked audio buffer management (0.5s chunks) | High |

### Agent Brain
- **Purpose:** Build context, generate responses, detect tool calls
- **Location:** `app/brain/`
- **Pattern:** Pipeline with context injection + streaming LLM

| File | Purpose | Priority |
|------|---------|----------|
| context_builder.py | Assembles prompt from memory + personality + history | High |
| llm_engine.py | Ollama streaming interface with tool-call detection | High |
| tool_parser.py | JSON action extraction from LLM output | High |
| personality.py | System prompt + personality configuration | Medium |

### Validation Layer
- **Purpose:** Safety-check actions before execution
- **Location:** `app/validation/`
- **Pattern:** Rule-based + LLM-based validation pipeline

| File | Purpose | Priority |
|------|---------|----------|
| action_validator.py | Validates actions (time checks, boundary checks) | Medium |
| safety_rules.py | Configurable safety rules | Medium |

### Execution Layer
- **Purpose:** Execute validated actions (reminders, tasks, calls)
- **Location:** `app/execution/`
- **Pattern:** Action dispatch with typed handlers

| File | Purpose | Priority |
|------|---------|----------|
| action_dispatcher.py | Routes actions to correct engine | High |
| reminder_engine.py | Time/condition-based reminder triggers | Medium |
| task_engine.py | Task CRUD operations | Medium |
| call_engine.py | Twilio call management | Low (Phase 4) |

### Output Layer
- **Purpose:** Convert text to speech, stream audio, handle barge-in
- **Location:** `app/output/`
- **Pattern:** Streaming TTS with interrupt support

| File | Purpose | Priority |
|------|---------|----------|
| tts_engine.py | Kokoro/Piper TTS streaming synthesis | High |
| audio_output.py | Audio playback with barge-in cancellation | High |

### Memory Layer
- **Purpose:** Persist conversations, enable semantic recall, compress history
- **Location:** `app/memory/`
- **Pattern:** Dual-store (structured + vector) with rolling compression

| File | Purpose | Priority |
|------|---------|----------|
| memory_service.py | Unified memory interface | High |
| vector_store.py | ChromaDB operations (store/query embeddings) | High |
| structured_store.py | SQLite operations (tasks, reminders, calls) | High |
| summary_engine.py | Rolling conversation summarizer | Medium |

### API Layer
- **Purpose:** FastAPI backend with WebSocket + REST endpoints
- **Location:** `app/api/`
- **Pattern:** Async FastAPI with WebSocket audio streams

| File | Purpose | Priority |
|------|---------|----------|
| main.py | FastAPI app entry point | High |
| routes/chat.py | /chat endpoint (text) | High |
| routes/audio.py | /stream-audio WebSocket | High |
| routes/tasks.py | /tasks CRUD endpoints | Medium |
| routes/reminders.py | /reminders CRUD endpoints | Medium |
| routes/calls.py | /call/* Twilio webhook endpoints | Low (Phase 4) |

## Data Flow

1. **Audio captured** from mic or Twilio stream
2. **VAD detects** speech start → STT begins transcription
3. **Context Builder** retrieves relevant memories from ChromaDB + last N messages
4. **LLM generates** streaming response (text or JSON action)
5. **Tool Parser** detects JSON → routes to Validation → Execution
6. **Text responses** → TTS streaming → audio output
7. **VAD detects** user interrupt → TTS stops immediately
8. **Memory saved** — conversation to ChromaDB, actions to SQLite

## Conventions

**Naming:**
- Services: `*_engine.py` or `*_service.py`
- Routes: `routes/*.py`
- Config: `app/config.py`

**Structure:**
- All async functions use `async def`
- All engines implement `start()` / `stop()` lifecycle
- All actions follow `{"action": str, ...params}` schema

---

*Last updated: 2026-04-13*
