import os
import logging
from functools import wraps
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from firebase_functions import https_fn

logger = logging.getLogger(__name__)

_twilio_client = None

def get_twilio_client() -> Client | None:
    """Initializes and returns a Twilio Client singleton."""
    global _twilio_client
    if _twilio_client is None:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        if account_sid and auth_token:
            _twilio_client = Client(account_sid, auth_token)
        else:
            logger.warning("Twilio Client requested but credentials are missing in env.")
            return None
    return _twilio_client

def validate_twilio_request(func):
    """Decorator to validate Twilio webhook requests."""
    @wraps(func)
    def wrapper(req: https_fn.Request, *args, **kwargs) -> https_fn.Response:
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        # If we don't have the auth token, we can't validate, so we skip or fail.
        # Let's fail if auth token is missing in production, but we can allow mock requests if emulated.
        if not auth_token:
            if os.environ.get("FUNCTIONS_EMULATOR") == "true":
                return func(req, *args, **kwargs)
            else:
                return https_fn.Response("Forbidden: Twilio Auth Token missing", status=403)

        validator = RequestValidator(auth_token)
        
        # Get the full URL (including query parameters)
        url = req.url
        
        # Get the POST parameters (only if it's a form request)
        post_vars = {}
        if req.method == "POST" and req.content_type == "application/x-www-form-urlencoded":
            post_vars = req.form.to_dict(flat=True)

        signature = req.headers.get("X-Twilio-Signature", "")

        if validator.validate(url, post_vars, signature):
            return func(req, *args, **kwargs)
        else:
            logger.warning(f"Twilio signature validation failed for URL: {url}")
            return https_fn.Response("Forbidden: Invalid Twilio Signature", status=403)
            
    return wrapper
