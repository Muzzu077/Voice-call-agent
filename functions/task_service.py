import os
import datetime
import logging
import requests
import json
import tempfile
from zoneinfo import ZoneInfo
from firebase_admin import firestore
from google.cloud.firestore import Client

logger = logging.getLogger(__name__)

def _build_llm_client():
    """Build an OpenAI-compatible client (OpenRouter or OpenAI)."""
    from openai import OpenAI

    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    kwargs = {"api_key": api_key}
    
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_api_key:
        kwargs["base_url"] = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        headers = {"X-Title": os.environ.get("OPENROUTER_APP_NAME", "VoiceCallAgent")}
        if os.environ.get("OPENROUTER_SITE_URL"):
            headers["HTTP-Referer"] = os.environ.get("OPENROUTER_SITE_URL")
        kwargs["default_headers"] = headers

    return OpenAI(**kwargs)

def download_recording(recording_url: str) -> str | None:
    """Downloads the audio recording from Twilio's public URL to a temporary local file."""
    logger.info(f"Downloading recording from Twilio.")
    try:
        auth = None
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        if account_sid and auth_token:
            auth = (account_sid, auth_token)
            
        response = requests.get(recording_url, auth=auth, stream=True, timeout=30)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        logger.error(f"Failed to download Twilio recording: {str(e)}")
        return None

def transcribe_audio(file_path: str) -> str:
    """Transcribes a local audio file using the OpenAI Whisper API."""
    if not os.environ.get("LLM_API_KEY") and not os.environ.get("OPENROUTER_API_KEY"):
        if os.environ.get("MOCK_MODE") == "true":
            logger.warning("No LLM API key configured. Returning simulated transcription.")
            return "I need to study AI neural networks today at 15:30. And tonight at 20:10 I want to work on my cybersecurity block."
        else:
            raise ValueError("LLM_API_KEY or OPENROUTER_API_KEY is not set.")
            
    if not file_path:
        raise ValueError("Audio file path is None.")
        
    try:
        client = _build_llm_client()
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=os.environ.get("OPENAI_TRANSCRIPTION_MODEL", "whisper-1"),
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        logger.error(f"Whisper transcription failed: {str(e)}")
        if os.environ.get("MOCK_MODE") == "true":
            return "Failed transcription fallback: study AI at 5:15 PM and cybersecurity at 8:10 PM."
        raise e

def parse_tasks(transcript: str, user_timezone_name: str = "UTC") -> list:
    """Parses a transcription string into structured tasks using OpenAI GPT in JSON mode."""
    try:
        tz = ZoneInfo(user_timezone_name)
    except Exception:
        tz = ZoneInfo("UTC")
        
    local_now = datetime.datetime.now(tz)
    today_str = local_now.strftime("%Y-%m-%d")
    local_time_str = local_now.strftime("%H:%M:%S")
    
    if not os.environ.get("LLM_API_KEY") and not os.environ.get("OPENROUTER_API_KEY"):
        if os.environ.get("MOCK_MODE") == "true":
            return [
                {
                    "description": "Study AI neural networks",
                    "iso_datetime": (local_now.replace(hour=15, minute=30, second=0, microsecond=0)).isoformat()
                }
            ]
        else:
            raise ValueError("LLM_API_KEY or OPENROUTER_API_KEY is not set.")
            
    try:
        client = _build_llm_client()
        system_prompt = (
            "You are a precise task extraction assistant. Your job is to extract a list of tasks "
            "from the user's transcribed morning call. For each task, extract:\n"
            "1. 'description': Concise task statement.\n"
            "2. 'iso_datetime': Absolute ISO 8601 datetime format (YYYY-MM-DDTHH:MM:SS) calculated in the "
            "user's local timezone.\n\n"
            "You MUST return only a valid JSON object with a single root key 'tasks' containing the array of task objects."
        )
        user_prompt = (
            f"User transcription: '{transcript}'\n"
            f"User local timezone: {user_timezone_name}\n"
            f"User current date today: {today_str}\n"
            f"User current local time: {local_time_str}\n"
        )
        
        model_name = os.environ.get("OPENROUTER_MODEL") or os.environ.get("OPENAI_TASK_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        parsed_json = json.loads(response.choices[0].message.content)
        return parsed_json.get("tasks", [])
    except Exception as e:
        logger.error(f"GPT task parsing failed: {str(e)}")
        return []

def process_recording_and_extract_tasks(db: Client, user_id: str, recording_url: str, call_sid: str = None) -> bool:
    """Pipeline to download, transcribe, parse, and save tasks to Firestore."""
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        logger.error(f"User {user_id} not found in database for task processing.")
        return False
        
    user_data = user_doc.to_dict()
    user_timezone = user_data.get("timezone", "UTC")
    
    local_path = download_recording(recording_url)
    if not local_path:
        logger.error("Download recording returned None.")
        return False
        
    try:
        transcript = transcribe_audio(local_path)
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        os.remove(local_path)
        return False
        
    try:
        os.remove(local_path)
    except Exception as e:
        logger.warning(f"Failed to delete temp file {local_path}: {e}")
            
    extracted_tasks = parse_tasks(transcript, user_timezone)
    
    try:
        tasks_ref = user_ref.collection("tasks")
        for item in extracted_tasks:
            desc = item.get("description", "Unnamed task")
            iso_dt_str = item.get("iso_datetime")
            
            scheduled_time = None
            if iso_dt_str:
                try:
                    dt = datetime.datetime.fromisoformat(iso_dt_str)
                    # Convert to UTC datetime before saving to Firestore
                    user_tz = ZoneInfo(user_timezone)
                    # For naive datetime
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=user_tz)
                    scheduled_time = dt.astimezone(ZoneInfo("UTC"))
                except Exception as e:
                    logger.warning(f"Could not parse iso_datetime string: {iso_dt_str}")
                    
            tasks_ref.add({
                "description": desc,
                "scheduled_time": scheduled_time,
                "is_completed": False,
                "reminder_sent": False,
                "call_sid": call_sid,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            
        logger.info(f"Processed {len(extracted_tasks)} tasks for User.")
        return True
    except Exception as e:
        logger.error(f"Failed to persist tasks to database: {str(e)}")
        return False
