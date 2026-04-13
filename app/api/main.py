"""
FastAPI Application — main entry point for the Voice Call AI Agent API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.brain.agent_service import AgentService
from app.input.audio_pipeline import AudioPipeline
from app.output.audio_output import AudioOutput
from app.output.tts_engine import TTSEngine
from app.api.routes import chat, tasks, reminders, audio, twilio, twilio_ws
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global singletons
agent = AgentService()
pipeline = AudioPipeline()
tts = TTSEngine()
audio_out = AudioOutput(tts)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize and shutdown."""
    # ── Startup ──────────────────────────────────────────
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(" Voice Call AI Agent - Starting Up")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    settings.ensure_data_dirs()
    await agent.initialize()
    pipeline.start()
    audio_out.start()

    # Inject agent + pipeline into route modules
    chat.set_agent(agent)
    tasks.set_agent(agent)
    reminders.set_agent(agent)
    audio.set_agent(agent)
    audio.set_pipeline(pipeline)
    audio.set_audio_output(audio_out)
    
    twilio_ws.set_agent(agent)
    twilio_ws.set_pipeline(pipeline)
    twilio_ws.set_audio_output(audio_out)

    logger.info(f" Agent ready | Model: {settings.OLLAMA_MODEL}")
    logger.info(f" Server: http://{settings.HOST}:{settings.PORT}")
    logger.info(f" Docs:   http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f" Audio WS: ws://{settings.HOST}:{settings.PORT}/ws/audio")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    yield

    # ── Shutdown ─────────────────────────────────────────
    logger.info("Shutting down...")
    pipeline.stop()
    audio_out.stop()
    await agent.shutdown()
    logger.info("Agent shut down. Goodbye.")


# ── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="Voice Call AI Agent",
    description="Real-time, interruptible, memory-aware AI voice agent API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(reminders.router)
app.include_router(audio.router)
app.include_router(twilio.router)
app.include_router(twilio_ws.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Voice Call AI Agent",
        "version": "0.1.0",
        "status": "running",
        "model": settings.OLLAMA_MODEL,
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    stats = agent.get_stats()
    return {
        "status": "healthy",
        "agent": stats,
    }
