import os
import json
import logging
import datetime
import secrets
import hmac
import hashlib
from zoneinfo import ZoneInfo
from firebase_functions import https_fn, pubsub_fn, scheduler_fn, identity_fn
from firebase_admin import initialize_app, firestore
from google.cloud import pubsub_v1
from twilio.twiml.voice_response import VoiceResponse

# Custom modules
import sip_service as sip
import task_service as tasks
from twilio_utils import validate_twilio_request

# Initialize Firebase Admin
if os.environ.get("FUNCTIONS_EMULATOR") == "true":
    import google.auth.credentials
    cred = google.auth.credentials.AnonymousCredentials()
    project_id = os.environ.get("GCLOUD_PROJECT") or os.environ.get("FIREBASE_PROJECT_ID") or "demo-project"
    initialize_app(cred, {'projectId': project_id})
else:
    initialize_app()

db = firestore.client()
logger = logging.getLogger(__name__)

# Constants
MAX_RECORDING_LENGTH = 45
DEDUPLICATION_WINDOW_MINUTES = 15

def sign_user_id(user_id: str) -> str:
    """Creates an HMAC signature for a user_id to prevent IDOR."""
    secret = os.environ.get("TWILIO_AUTH_TOKEN", "default-secret").encode("utf-8")
    sig = hmac.new(secret, user_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"

def verify_user_id(token: str) -> str | None:
    """Verifies HMAC signature and returns user_id if valid."""
    if not token or "." not in token:
        return None
    user_id, sig = token.split(".", 1)
    expected_sig = hmac.new(
        os.environ.get("TWILIO_AUTH_TOKEN", "default-secret").encode("utf-8"),
        user_id.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return user_id if hmac.compare_digest(sig, expected_sig) else None

# --- Auth Trigger ---

@identity_fn.before_user_created()
def on_user_created(event: identity_fn.AuthBlockingEvent) -> identity_fn.BeforeCreateResponse | None:
    """Triggered when a new user signs up in Firebase Auth."""
    uid = event.data.uid
    email = event.data.email
    
    # 1. Provision a Twilio SIP Credential
    username = f"user_{uid[:10].lower()}"
    password = secrets.token_urlsafe(16)
    sip_uri = sip.create_sip_credential(username, password)
    
    # 2. Create default user profile in Firestore
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "email": email,
        "timezone": "UTC",
        "morning_call_time": "08:00",
        "next_morning_call_utc": firestore.SERVER_TIMESTAMP,
        "created_at": firestore.SERVER_TIMESTAMP,
        "sip_uri": sip_uri  # Denormalized
    })
    
    # 3. Save credential to subcollection
    user_ref.collection("sip_credentials").document("main").set({
        "username": username,
        "password": password, # User needs to see this once in dashboard to configure softphone
        "sip_uri": sip_uri,
        "active": True
    })
    
    # 4. Create sip username index for fast lookups
    db.collection("sip_username_index").document(username).set({
        "user_id": uid
    })
    
    logger.info(f"Provisioned SIP credential for new user {uid}")
    return None

# --- Twilio Webhooks ---

@https_fn.on_request()
@validate_twilio_request
def voice_incoming(req: https_fn.Request) -> https_fn.Response:
    """Incoming SIP webhook."""
    response = VoiceResponse()
    from_uri = req.form.get("From", "")
    user_id = None
    
    if "sip:" in from_uri:
        try:
            sip_part = from_uri.split("sip:")[1]
            username = sip_part.split("@")[0]
            
            # Fast O(1) lookup
            idx_doc = db.collection("sip_username_index").document(username).get()
            if idx_doc.exists:
                user_id = idx_doc.to_dict().get("user_id")
        except Exception as e:
            logger.error(f"Error parsing incoming caller URI: {e}")

    if user_id:
        token = sign_user_id(user_id)
        response.say("Welcome back! Please speak your agenda and daily tasks after the beep. Press hash when finished.")
        response.record(
            action=f"/voice_recording_callback?token={token}",
            maxLength=MAX_RECORDING_LENGTH,
            playBeep=True,
            finishOnKey="#"
        )
    else:
        response.say("Welcome. We could not identify your SIP credentials. Goodbye.")
        response.hangup()
        
    return https_fn.Response(str(response), content_type='application/xml')

@https_fn.on_request()
@validate_twilio_request
def voice_morning_call(req: https_fn.Request) -> https_fn.Response:
    """Outbound TwiML morning call response greeting and recording prompt."""
    token = req.args.get("token")
    user_id = verify_user_id(token)
    response = VoiceResponse()
    
    if user_id:
        response.say("Good morning! This is your personal assistant. Please tell me your agenda and scheduled study blocks for today after the tone.")
        response.record(
            action=f"/voice_recording_callback?token={token}",
            maxLength=MAX_RECORDING_LENGTH,
            playBeep=True
        )
    else:
        response.say("System error: User identification failed. Goodbye.")
        response.hangup()
        
    return https_fn.Response(str(response), content_type='application/xml')

@https_fn.on_request()
@validate_twilio_request
def voice_recording_callback(req: https_fn.Request) -> https_fn.Response:
    """Receives recording url, acknowledges, and triggers pubsub for processing."""
    token = req.args.get('token')
    user_id = verify_user_id(token)
    recording_url = req.form.get('RecordingUrl')
    call_sid = req.form.get('CallSid')
    
    response = VoiceResponse()
    
    if not user_id or not recording_url:
        logger.warning(f"Missing valid user_id or recording_url. User_id identified: {user_id}")
        response.say("We encountered an error processing your recording. Please try again.")
        response.hangup()
        return https_fn.Response(str(response), content_type='application/xml')
        
    # Publish message to Pub/Sub to process in background
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ.get("GCLOUD_PROJECT", "demo-project"), "process_recording")
    
    payload = {
        "user_id": user_id,
        "recording_url": recording_url,
        "call_sid": call_sid
    }
    publisher.publish(topic_path, json.dumps(payload).encode("utf-8"))
        
    response.say("I have recorded your agenda. Processing your tasks now. Have an exceptional and productive day!")
    response.hangup()
    return https_fn.Response(str(response), content_type='application/xml')

@pubsub_fn.on_message_published(topic="process_recording")
def process_recording_background(event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData]) -> None:
    """Background worker to parse transcription and save tasks to Firestore."""
    try:
        payload = json.loads(event.data.message.data.decode("utf-8"))
        user_id = payload.get("user_id")
        recording_url = payload.get("recording_url")
        call_sid = payload.get("call_sid")
        
        tasks.process_recording_and_extract_tasks(db, user_id, recording_url, call_sid)
    except Exception as e:
        logger.error(f"Failed to process background recording task: {e}")
        # Not re-raising avoids infinite retries if it's a poison pill

@https_fn.on_request()
@validate_twilio_request
def voice_reminder_call(req: https_fn.Request) -> https_fn.Response:
    """TwiML Webhook played when reminder SIP call connects."""
    token = req.args.get('token')
    user_id = verify_user_id(token)
    task_id = req.args.get('task_id')
    
    response = VoiceResponse()
    
    if user_id and task_id:
        task_ref = db.collection("users").document(user_id).collection("tasks").document(task_id)
        task_doc = task_ref.get()
        if task_doc.exists:
            task = task_doc.to_dict()
            response.say(f"Greetings! This is your dynamic task reminder: Time to start: {task.get('description')}.")
            response.say("I repeat: Time to start: " + task.get('description'))
            # Mark reminder delivered, not completed
            task_ref.update({"reminder_delivered": True})
        else:
            response.say("Greetings! This is your scheduled planner reminder call.")
    else:
        response.say("Greetings! You have a scheduled task reminder.")
        
    response.hangup()
    return https_fn.Response(str(response), content_type='application/xml')

@https_fn.on_request()
@validate_twilio_request
def voice_status_callback(req: https_fn.Request) -> https_fn.Response:
    """Twilio Status Callback to track call connection state."""
    call_sid = req.form.get('CallSid')
    call_status = req.form.get('CallStatus')
    
    if call_sid:
        idx_doc = db.collection("call_sid_index").document(call_sid).get()
        if idx_doc.exists:
            idx_data = idx_doc.to_dict()
            user_id = idx_data.get("user_id")
            log_id = idx_data.get("log_id")
            if user_id and log_id:
                db.collection("users").document(user_id).collection("call_logs").document(log_id).update({
                    "status": call_status
                })
                
    return https_fn.Response("OK", status=200)

# --- Scheduler (Cron) ---

@scheduler_fn.on_schedule(schedule="*/5 * * * *")
def scheduler_cron(event: scheduler_fn.ScheduledEvent) -> None:
    """Runs every 5 minutes to dispatch morning calls and task reminders."""
    utc_now = datetime.datetime.now(ZoneInfo("UTC"))
    
    # 1. Dispatch Morning Calls (Optimized via index)
    due_users = db.collection("users").where("next_morning_call_utc", "<=", utc_now).get()
    
    for u in due_users:
        user_data = u.to_dict()
        user_id = u.id
        timezone_str = user_data.get("timezone", "UTC")
        morning_time = user_data.get("morning_call_time", "08:00")
        
        try:
            user_tz = ZoneInfo(timezone_str)
            user_local_time = utc_now.astimezone(user_tz)
            current_hh_mm = user_local_time.strftime("%H:%M")
            
            # Since we only fetch due users, we check if their local time has hit morning call time
            if current_hh_mm >= morning_time:
                sip_uri = user_data.get("sip_uri")
                if sip_uri:
                    token = sign_user_id(user_id)
                    twiml_url = f"{os.environ.get('BASE_URL', '')}/voice_morning_call?token={token}"
                    call_sid = sip.trigger_outbound_sip_call_to_uri(sip_uri, twiml_url)
                    if call_sid:
                        _, doc_ref = u.reference.collection("call_logs").add({
                            "call_sid": call_sid,
                            "direction": "outbound",
                            "status": "initiated",
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        # Add to fast index
                        db.collection("call_sid_index").document(call_sid).set({
                            "user_id": user_id,
                            "log_id": doc_ref.id
                        })
                        
                # Schedule for next day
                next_call_dt = utc_now + datetime.timedelta(days=1)
                u.reference.update({"next_morning_call_utc": next_call_dt})
                
        except Exception as e:
            logger.error(f"Error processing morning call for user {user_id}: {e}")

    # 2. Dispatch Task Reminders (We still need to find tasks that are due)
    # To optimize this further without full user scan, we could use a collectionGroup query on tasks.
    due_tasks = db.collection_group("tasks") \
                  .where("is_completed", "==", False) \
                  .where("reminder_sent", "==", False) \
                  .where("scheduled_time", "<=", utc_now) \
                  .get()
                  
    for task_doc in due_tasks:
        try:
            # Mark reminder_sent immediately
            task_doc.reference.update({"reminder_sent": True})
            
            user_id = task_doc.reference.parent.parent.id
            user_ref = db.collection("users").document(user_id)
            user_data = user_ref.get().to_dict()
            sip_uri = user_data.get("sip_uri")
            
            if sip_uri:
                token = sign_user_id(user_id)
                twiml_url = f"{os.environ.get('BASE_URL', '')}/voice_reminder_call?token={token}&task_id={task_doc.id}"
                call_sid = sip.trigger_outbound_sip_call_to_uri(sip_uri, twiml_url)
                if call_sid:
                    _, log_ref = user_ref.collection("call_logs").add({
                        "call_sid": call_sid,
                        "direction": "outbound",
                        "status": "initiated",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    db.collection("call_sid_index").document(call_sid).set({
                        "user_id": user_id,
                        "log_id": log_ref.id
                    })
        except Exception as e:
            logger.error(f"Error processing task reminder for task {task_doc.id}: {e}")
