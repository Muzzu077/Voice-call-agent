"""
Twilio Basic Webhooks.
Handles standard HTTP callbacks from Twilio for incoming calls.
"""

import logging
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/call", tags=["Twilio"])

@router.post("/incoming")
async def handle_incoming_call(request: Request):
    """
    Webhook for incoming phone calls from Twilio.
    Returns TwiML telling Twilio to connect a Media Stream (WebSocket) to our server.
    """
    logger.info("Incoming Twilio call received.")
    
    # We must deduce our public host (from ngrok/localtunnel) from the request headers
    # since Twilio uses it to send the HTTP webhook.
    host = request.headers.get("host")
    scheme = "wss" if request.headers.get("x-forwarded-proto", "http") == "https" else "ws"
    
    ws_url = f"{scheme}://{host}/ws/twilio"
    
    # Generate standard TwiML to open a bidirectional media stream to our websocket
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>"""

    return Response(content=twiml_response, media_type="text/xml")

@router.post("/sms")
async def handle_sms(request: Request):
    """
    Webhook for incoming SMS messages.
    """
    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>The Voice Call AI Agent is currently focused on voice. SMS is disabled.</Message>
</Response>"""
    return Response(content=twiml_response, media_type="text/xml")
