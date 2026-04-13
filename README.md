# Voice Call AI Agent

A real-time, interruptible, memory-aware AI voice agent that talks naturally, handles phone calls, executes actions via tool calling, remembers intelligently, and behaves safely.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
copy .env.example .env

# 4. Ensure Ollama is running with a model
ollama pull llama3.1

# 5. Run the server
python run.py
```

## Architecture

See [.gsd/ARCHITECTURE.md](.gsd/ARCHITECTURE.md) for the full system design.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /chat | Send a text message, get AI response |
| GET | /chat/history | Get recent conversation history |
| POST | /tasks | Create a task |
| GET | /tasks | List all tasks |
| POST | /reminders | Create a reminder |
| GET | /reminders | List all reminders |

## Tech Stack

- **LLM:** Ollama (Llama 3.1 / Qwen 3)
- **STT:** Faster-Whisper
- **TTS:** Kokoro TTS / Piper TTS
- **VAD:** Silero VAD
- **Vector DB:** ChromaDB
- **Structured DB:** SQLite
- **API:** FastAPI + WebSockets
- **Telephony:** Twilio

## Development Phases

1. ✅ Foundation — LLM + Memory + Tool Calling
2. ⬜ Audio Pipeline — VAD + Streaming STT
3. ⬜ Voice Output — TTS + Real-Time Loop
4. ⬜ Telephony — Twilio Integration
5. ⬜ Intelligence — Summarization + Validation

## License

MIT
