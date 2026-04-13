# Architecture Decision Records

## ADR-001: Local LLM via Ollama
**Date:** 2026-04-13
**Status:** Accepted
**Context:** Need an LLM for conversational AI with tool-calling and streaming support.
**Decision:** Use Ollama with Llama 3.1+ or Qwen 3 models locally.
**Rationale:** No cloud dependency, free, supports streaming + native tool calling, privacy-preserving.
**Consequences:** Requires local GPU for good performance. Model quality depends on hardware.

## ADR-002: Dual Memory Architecture
**Date:** 2026-04-13
**Status:** Accepted
**Context:** Agent needs both structured data (tasks, reminders) and semantic recall (conversation context).
**Decision:** SQLite for structured data + ChromaDB for vector/semantic memory.
**Rationale:** SQLite is zero-config and reliable. ChromaDB provides embedded vector search without external services.
**Consequences:** Two data stores to maintain. Need embedding model for ChromaDB.

## ADR-003: Silero VAD Lite for Speech Detection
**Date:** 2026-04-13
**Status:** Accepted
**Context:** Need real-time voice activity detection with minimal latency.
**Decision:** Use silero-vad-lite (ONNX-based, no PyTorch dependency).
**Rationale:** Lightweight, CPU-efficient, 16kHz support, well-documented for real-time use.
**Consequences:** Only supports 8kHz/16kHz sample rates.

## ADR-004: Kokoro TTS as Primary, Piper as Fallback
**Date:** 2026-04-13
**Status:** Accepted
**Context:** Need low-latency, open-source TTS for real-time voice output.
**Decision:** Kokoro TTS primary (best quality/speed balance), Piper TTS fallback (ultra-lightweight).
**Rationale:** Kokoro is the current leader in open-source TTS quality. Piper runs on CPU with minimal resources.
**Consequences:** May need to test both and pick based on actual hardware performance.

## ADR-005: FastAPI + WebSockets for Real-Time Backend
**Date:** 2026-04-13
**Status:** Accepted
**Context:** Need async web framework supporting both REST APIs and real-time audio streams.
**Decision:** FastAPI with native WebSocket support.
**Rationale:** Best Python async framework. Native WebSocket support. Automatic OpenAPI docs. Pydantic validation built-in.
**Consequences:** Must use async patterns throughout. Uvicorn as ASGI server.
