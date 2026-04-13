"""
WebSocket Audio Route — real-time audio streaming endpoint.

Protocol:
  Client → Server : raw 16-bit PCM audio bytes at 16kHz mono (chunked)
  Server → Client : JSON messages with transcriptions and AI responses

Message types (server → client):
  {"type": "transcript",  "text": "...", "confidence": 0.9}
  {"type": "response",    "text": "..."}
  {"type": "state",       "state": "listening|buffering|processing"}
  {"type": "interrupt",   "message": "AI stopped"}
  {"type": "error",       "message": "..."}
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["Audio"])

# Injected at startup
_agent = None
_pipeline = None
_audio_output = None


def set_agent(agent):
    global _agent
    _agent = agent


def set_pipeline(pipeline):
    global _pipeline
    _pipeline = pipeline


def set_audio_output(audio_output):
    global _audio_output
    _audio_output = audio_output


@router.websocket("/audio")
async def audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming.

    Clients send raw 16-bit PCM audio bytes at 16kHz mono.
    Server returns JSON messages with transcriptions and AI responses.
    """
    await websocket.accept()
    client = websocket.client
    logger.info(f"WebSocket connected: {client}")

    if _pipeline is None or _agent is None:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Audio pipeline not initialized."
        }))
        await websocket.close()
        return

    # Per-connection pipeline (reuses global but sets callbacks per connection)
    pipeline = _pipeline

    async def on_transcript(text: str, confidence: float):
        """Called when speech is transcribed — send to agent, speak response."""
        # Send transcript ack to client
        await websocket.send_text(json.dumps({
            "type": "transcript",
            "text": text,
            "confidence": round(confidence, 2),
        }))

        # Process through agent
        pipeline.set_ai_speaking(True)
        try:
            result = await _agent.process_message(text)
            response_text = result["response"]

            # Send response to client (for UI display)
            await websocket.send_text(json.dumps({
                "type": "response",
                "text": response_text,
                "action": result.get("action"),
                "action_result": result.get("action_result"),
            }))

            # Speak through TTS if audio_output is available
            if _audio_output and response_text:
                await _audio_output.speak(response_text)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        finally:
            pipeline.set_ai_speaking(False)

    async def on_interrupt():
        """Called on barge-in — stop TTS and notify client."""
        if _audio_output:
            _audio_output.interrupt()
        await websocket.send_text(json.dumps({
            "type": "interrupt",
            "message": "AI speech interrupted by user.",
        }))

    async def on_state_change(state: str):
        """Called on pipeline state changes."""
        await websocket.send_text(json.dumps({
            "type": "state",
            "state": state,
        }))

    # Register callbacks
    pipeline.on_transcript(on_transcript)
    pipeline.on_interrupt(on_interrupt)
    pipeline.on_state_change(on_state_change)

    # Send ready signal
    await websocket.send_text(json.dumps({
        "type": "state",
        "state": "connected",
        "message": "Audio pipeline ready. Send 16kHz mono 16-bit PCM chunks.",
    }))

    try:
        while True:
            # Receive audio chunk (binary) or control message (text)
            data = await websocket.receive()

            if "bytes" in data and data["bytes"]:
                # Audio chunk — process through pipeline
                audio_bytes = data["bytes"]
                await pipeline.process_chunk(audio_bytes, sample_width=2)

            elif "text" in data and data["text"]:
                # Control message (JSON)
                try:
                    msg = json.loads(data["text"])
                    msg_type = msg.get("type", "")

                    if msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))

                    elif msg_type == "text_message":
                        # Allow text input over WebSocket too
                        text = msg.get("text", "").strip()
                        if text and _agent:
                            result = await _agent.process_message(text)
                            await websocket.send_text(json.dumps({
                                "type": "response",
                                "text": result["response"],
                                "action": result.get("action"),
                            }))

                    elif msg_type == "set_speaking":
                        # Client tells us AI audio is playing/stopped
                        pipeline.set_ai_speaking(msg.get("speaking", False))

                except json.JSONDecodeError:
                    pass  # Ignore malformed messages

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        logger.info(f"WebSocket session ended: {client}")
