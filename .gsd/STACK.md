# Technology Stack

> Generated on 2026-04-13

## Runtime

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core runtime |
| FastAPI | 0.115+ | Async web framework |
| SQLite | 3.x | Structured data storage |
| ChromaDB | 0.5+ | Vector database for semantic memory |

## Core Technologies

### AI / ML Pipeline

| Feature | System | Purpose |
|---------|--------|---------|
| Voice Activity Detection | Silero VAD (silero-vad-lite) | Real-time speech detection, barge-in |
| Speech-to-Text | faster-whisper | Streaming audio transcription |
| Large Language Model | Ollama (Llama 3.1 / Qwen 3) | Conversational AI + tool calling |
| Text-to-Speech | Kokoro TTS / Piper TTS | Low-latency voice synthesis |
| Embeddings | sentence-transformers | ChromaDB embedding generation |

### Backend

| Feature | System | Purpose |
|---------|--------|---------|
| API Framework | FastAPI | REST + WebSocket endpoints |
| Real-time | WebSockets + asyncio | Audio streaming, real-time comms |
| Task Scheduling | APScheduler | Reminder/timer triggers |
| Telephony | Twilio | Phone call integration (Phase 4) |

### Data Storage

| Directory | Purpose |
|-----------|---------|
| `data/voice_agent.db` | SQLite — tasks, reminders, call logs |
| `data/chroma/` | ChromaDB — conversation embeddings |

## Dependencies

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | ^0.115 | Web framework |
| uvicorn | ^0.30 | ASGI server |
| websockets | ^12.0 | WebSocket support |
| ollama | ^0.4 | Ollama Python client |
| chromadb | ^0.5 | Vector database |
| silero-vad-lite | ^1.0 | Voice activity detection |
| faster-whisper | ^1.0 | Speech-to-text |
| kokoro | ^0.9 | Text-to-speech |
| pydantic | ^2.0 | Data validation |
| apscheduler | ^3.10 | Task scheduling |
| sounddevice | ^0.5 | Audio I/O |
| numpy | ^1.26 | Audio processing |
| sentence-transformers | ^3.0 | Embedding generation |
| twilio | ^9.0 | Telephony SDK (Phase 4) |

### Internal Dependencies

| Component | Depends On | Purpose |
|-----------|------------|---------|
| Agent Brain | Memory Layer | Context retrieval for prompts |
| Agent Brain | Input Layer | Receives transcriptions |
| Execution Layer | Validation Layer | Actions validated before execution |
| Output Layer | Agent Brain | Receives text responses to synthesize |
| Memory Layer | Agent Brain | Stores conversation history |
| API Layer | All components | Orchestrates the full pipeline |

## Configuration

| Variable | Purpose | Location |
|----------|---------|----------|
| OLLAMA_MODEL | LLM model name | .env |
| OLLAMA_BASE_URL | Ollama server URL | .env |
| WHISPER_MODEL_SIZE | Whisper model (tiny/base/small) | .env |
| TTS_ENGINE | TTS backend (kokoro/piper) | .env |
| CHROMA_PERSIST_DIR | ChromaDB storage path | .env |
| SQLITE_DB_PATH | SQLite database path | .env |
| TWILIO_ACCOUNT_SID | Twilio credentials | .env |
| TWILIO_AUTH_TOKEN | Twilio credentials | .env |
| TWILIO_PHONE_NUMBER | Twilio phone number | .env |
| VAD_THRESHOLD | Speech detection sensitivity | .env |
| AUDIO_SAMPLE_RATE | Audio sample rate (16000) | .env |

---

*Last updated: 2026-04-13*
