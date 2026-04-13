"""
Application configuration — loads from .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── LLM ──────────────────────────────────────────────
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ── Whisper STT (Phase 2) ────────────────────────────
    WHISPER_MODEL_SIZE: str = "base"

    # ── TTS (Phase 3) ───────────────────────────────────
    TTS_ENGINE: str = "kokoro"

    # ── Memory ───────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    SQLITE_DB_PATH: str = "./data/voice_agent.db"

    # ── Audio ────────────────────────────────────────────
    VAD_THRESHOLD: float = 0.5
    AUDIO_SAMPLE_RATE: int = 16000

    # ── Twilio (Phase 4) ────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── Server ───────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_data_dirs(self):
        """Create data directories if they don't exist."""
        Path(self.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
