import os
import logging
from twilio_utils import get_twilio_client

logger = logging.getLogger(__name__)

def create_sip_credential(username: str, password: str) -> str | None:
    """
    Registers a new SIP credential with the Twilio SIP Credential List.
    Returns the sip_uri if successful, or None on failure.
    """
    sip_domain = os.environ.get("TWILIO_SIP_DOMAIN", "planner.sip.twilio.com")
    full_sip_uri = f"sip:{username}@{sip_domain}"
    
    twilio_cred_list_sid = os.environ.get("TWILIO_CREDENTIAL_LIST_SID")
    twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    
    if not twilio_cred_list_sid or not twilio_account_sid:
        logger.warning(
            f"Twilio Credential List SID not configured. Stubbing SIP registration for '{username}' locally."
        )
        return full_sip_uri
        
    try:
        client = get_twilio_client()
        if not client:
            return None
        credential = client.sip \
            .credential_lists(twilio_cred_list_sid) \
            .credentials \
            .create(username=username, password=password)
            
        logger.info(f"Successfully registered Twilio SIP credential: SID={credential.sid}")
        return full_sip_uri
        
    except Exception as e:
        logger.error(f"Failed to create Twilio SIP credential: {str(e)}")
        return None

def trigger_outbound_sip_call_to_uri(sip_uri: str, twiml_url: str) -> str | None:
    """
    Triggers an outbound SIP call using the Twilio REST API directly to a SIP URI.
    """
    sip_domain = os.environ.get("TWILIO_SIP_DOMAIN", "planner.sip.twilio.com")
    from_identity = os.environ.get("TWILIO_PHONE_NUMBER", f"sip:assistant@{sip_domain}")
    
    logger.info(f"Initiating outbound SIP call using TwiML URL: {twiml_url}")
    
    if not os.environ.get("TWILIO_ACCOUNT_SID") or not os.environ.get("TWILIO_AUTH_TOKEN"):
        logger.warning(
            f"[MOCK CALL] Dispatching mock outbound call to '{sip_uri}' (Twilio credentials missing)."
        )
        import uuid
        return f"MC-{uuid.uuid4().hex[:12]}"
        
    try:
        client = get_twilio_client()
        if not client:
            return None
            
        base_url = os.environ.get("BASE_URL", "")
        status_callback_url = f"{base_url}/voice_status_callback"
        
        call = client.calls.create(
            url=twiml_url,
            to=sip_uri,
            from_=from_identity,
            status_callback=status_callback_url,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        logger.info(f"Twilio call dispatched successfully. CallSid={call.sid}, Status={call.status}")
        return call.sid
    except Exception as e:
        logger.error(f"Failed to dispatch Twilio SIP call: {str(e)}")
        return None
