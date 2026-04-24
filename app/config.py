"""
Application configuration — loads from .env file.
SaaS-grade settings for the AI Voice + Desktop Agent Platform.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ─────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://agent:agent_secret_2026@localhost:5432/voiceagent"

    # ── Auth ─────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # ── LLM ──────────────────────────────────────
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ── ChromaDB ─────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    # Legacy local path (fallback if CHROMA_HOST not reachable)
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # ── Whisper STT ──────────────────────────────
    WHISPER_MODEL_SIZE: str = "base.en"

    # ── TTS ──────────────────────────────────────
    TTS_ENGINE: str = "kokoro"

    # ── Audio ────────────────────────────────────
    VAD_THRESHOLD: float = 0.5
    AUDIO_SAMPLE_RATE: int = 16000

    # ── Twilio ───────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_CALLBACK_NUMBER: str = ""

    # ── Server ───────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Legacy (kept for backward compat) ────────
    SQLITE_DB_PATH: str = "./data/voice_agent.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_data_dirs(self):
        """Create data directories if they don't exist."""
        Path(self.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
