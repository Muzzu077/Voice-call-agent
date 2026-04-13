"""Verification script for Phase 4 — Telephony Integration."""
import sys
import asyncio
import base64
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    print("=" * 50)
    print("Phase 4 Verification — Telephony")
    print("=" * 50)

    # 1. Audio Utils
    print("\n[1] Audio Utils Conversion...")
    from app.input.audio_utils import float32_24khz_to_mulaw, mulaw_to_float32_16khz
    # Create fake 24kHz float32 audio (1 second of zeros)
    dummy_audio = np.zeros(24000, dtype=np.float32)
    mulaw_bytes = float32_24khz_to_mulaw(dummy_audio)
    
    # 24000 PCM samples resampled to 8kHz should yield exactly 8000 mu-law bytes
    print(f"  24kHz to_mulaw output size: {len(mulaw_bytes)} bytes")
    assert len(mulaw_bytes) == 8000
    
    # Send it back through the 16kHz decoder
    restored_float32 = mulaw_to_float32_16khz(mulaw_bytes)
    # 8000 mu-law bytes decoded & resampled to 16kHz should yield 16000 float32 samples
    print(f"  mulaw_to 16kHz float32 size: {len(restored_float32)} samples (dtype: {restored_float32.dtype})")
    assert len(restored_float32) == 16000
    assert restored_float32.dtype == np.float32
    print("  [OK] audio_utils (mu-law resampling works)")

    # 2. Twilio Router (Webhooks)
    print("\n[2] Twilio Webhook Router...")
    from app.api.routes.twilio import router
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    import sys
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Emulate incoming call from Twilio
    response = client.post("/call/incoming", headers={"host": "test.ngrok.app", "x-forwarded-proto": "https"})
    print(f"  /call/incoming status: {response.status_code}")
    print(f"  /call/incoming Response: \n{response.text.strip()}")
    assert response.status_code == 200
    assert "wss://test.ngrok.app/ws/twilio" in response.text
    assert "<Connect>" in response.text and "<Stream" in response.text
    print("  [OK] Twilio XML Webhook")

    # 3. Main app injection verification
    print("\n[3] Main app routing...")
    from app.api.main import app as main_app
    routes = [r.path for r in main_app.routes]
    assert "/call/incoming" in routes
    assert "/ws/twilio" in routes
    print(f"  Total routes: {len(routes)}")
    print("  [OK] FastAPI app updated")
    
    print("\n" + "=" * 50)
    print("ALL PHASE 4 COMPONENTS VERIFIED")
    print("=" * 50)
    print("\nNOTE: Ensure ngrok is running and Twilio console has the webhook URL.")

if __name__ == "__main__":
    asyncio.run(main())
