"""
Twilio Media Streams WebSocket router.
Handles the bidirectional audio stream during an active phone call.
"""

import json
import base64
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.input.audio_utils import mulaw_to_float32_16khz, float32_24khz_to_mulaw

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["Twilio Media Streams"])

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

@router.websocket("/twilio")
async def twilio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.
    Receives base64-encoded mulaw (8kHz) audio from the caller.
    Sends base64-encoded mulaw (8kHz) audio synthesized by the AI.
    """
    await websocket.accept()
    stream_sid = None
    logger.info("Twilio Media Stream WebSocket connected.")

    if not _pipeline or not _agent or not _audio_output:
        logger.error("System components not fully initialized for Twilio.")
        await websocket.close()
        return

    # Use a per-connection flag/task map to handle concurrent playback cleanly
    play_task = None

    async def send_audio_to_twilio(text: str):
        """Synthesize text and stream it over the WebSocket to Twilio."""
        try:
            async for chunk in _audio_output.stream(text):
                # chunk is 24kHz float32 from Kokoro
                mulaw_bytes = float32_24khz_to_mulaw(chunk)
                if not mulaw_bytes:
                    continue
                
                # Base64 encode and package in Twilio JSON format
                payload = base64.b64encode(mulaw_bytes).decode("utf-8")
                msg = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": payload
                    }
                }
                await websocket.send_text(json.dumps(msg))
                
                # Small sleep to allow async event loop to breathe during playback
                # In production, we'd pace this based on the exact audio duration to avoid buffering issues
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error streaming audio to Twilio: {e}")

    async def on_transcript(text: str, confidence: float):
        """Fired by AudioPipeline when caller finishes speaking."""
        nonlocal play_task
        
        # Stop any existing AI playback if the user spoke (Barge-in behavior)
        if play_task and not play_task.done():
            play_task.cancel()
            
        # Optional: Send a "clear" message to Twilio to halt any buffered audio on their end
        if stream_sid:
            await websocket.send_text(json.dumps({"event": "clear", "streamSid": stream_sid}))

        _pipeline.set_ai_speaking(True)
        try:
            # Send to LLM
            result = await _agent.process_message(text)
            response_text = result["response"]
            
            # Start streaming audio back to caller
            if response_text:
                play_task = asyncio.create_task(send_audio_to_twilio(response_text))
                
        except Exception as e:
            logger.error(f"Twilio Agent error: {e}")
        finally:
            _pipeline.set_ai_speaking(False)

    async def on_interrupt():
        """Fired by AudioPipeline on barge-in."""
        nonlocal play_task
        if play_task and not play_task.done():
            play_task.cancel()
        
        # Clear Twilio's playback buffer immediately
        if stream_sid:
            await websocket.send_text(json.dumps({"event": "clear", "streamSid": stream_sid}))
            
    # Swap out the existing callbacks with our Twilio specific ones for this session
    # (Note: In a multi-tenant production system, you'd instantiate a new pipeline per call)
    _pipeline.on_transcript(on_transcript)
    _pipeline.on_interrupt(on_interrupt)
    
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            event = data.get("event")

            if event == "start":
                stream_sid = data["start"]["streamSid"]
                logger.info(f"Twilio Stream Started: {stream_sid}")
                
            elif event == "media":
                # Decode Twilio mulaw base64 payload
                payload = data["media"]["payload"]
                mulaw_bytes = base64.b64decode(payload)
                
                # Convert to numpy float32 arrays (16kHz) for our VAD and STT
                audio_f32 = mulaw_to_float32_16khz(mulaw_bytes)
                
                # Feed the Audio Pipeline
                await _pipeline.process_numpy_chunk(audio_f32)
                
            elif event == "stop":
                logger.info("Twilio Stream Stopped by Caller.")
                break

    except WebSocketDisconnect:
        logger.info("Twilio WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Twilio WebSocket error: {e}")
    finally:
        if play_task and not play_task.done():
            play_task.cancel()
