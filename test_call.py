import os
import sys
import time
import requests
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def get_ngrok_url():
    """Try to find the public ngrok URL via the local API."""
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get("tunnels", []):
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
    except Exception:
        pass
    return None

def trigger_outbound_call(to_number):
    """Triggers an outbound call from Twilio to the user."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_number]):
        print("Error: TWILIO_ACCOUNT_SID, AUTH_TOKEN, or PHONE_NUMBER missing from .env")
        return

    # 1. Get Ngrok URL
    public_url = get_ngrok_url()
    if not public_url:
        print("--- ACTION REQUIRED ---")
        public_url = input("Could not auto-detect Ngrok URL. Please paste your Ngrok HTTPS URL: ").strip()
    
    # Clean up URL (remove trailing slash)
    if public_url.endswith("/"):
        public_url = public_url[:-1]
    
    webhook_url = f"{public_url}/call/incoming"
    print(f"Using Webhook URL: {webhook_url}")

    # 2. Initialize Twilio Client
    client = Client(account_sid, auth_token)

    try:
        print(f"Initiating call to {to_number} from {from_number}...")
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=webhook_url
        )
        print(f"Call successfully triggered! SID: {call.sid}")
        print("Please wait for your phone to ring...")
    except Exception as e:
        print(f"Failed to trigger call: {e}")

if __name__ == "__main__":
    # Your verified Indian number
    target_number = "+918074708433"
    
    print("=== Twilio Outbound Test Script ===")
    trigger_outbound_call(target_number)
