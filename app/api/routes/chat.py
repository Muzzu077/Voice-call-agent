"""
Chat routes — /chat endpoint for text-based interaction with the AI agent.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.memory.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# Agent service will be injected at startup
_agent = None


def set_agent(agent):
    """Inject the agent service instance."""
    global _agent
    _agent = agent


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI agent and get a response.

    The agent will:
    1. Retrieve relevant context from memory
    2. Generate a response (or execute an action)
    3. Save the conversation to memory
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.process_message(request.message)
        return ChatResponse(
            response=result["response"],
            action=result.get("action"),
            action_result=result.get("action_result"),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a message and stream the response token-by-token.
    Returns a text/event-stream response.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    async def generate():
        try:
            async for token in _agent.process_message_stream(request.message):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history")
async def get_history():
    """Get the current conversation history."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {"history": _agent.get_conversation_history()}


@router.get("/stats")
async def get_stats():
    """Get agent statistics (memory count, session info, etc)."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return _agent.get_stats()
