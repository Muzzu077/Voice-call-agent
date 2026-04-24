"""
Reminder Scheduler — polls SQLite every 30 seconds for due reminders
and places an outbound Twilio call to the user to deliver them.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# IST offset for Indian Standard Time
IST = timezone(timedelta(hours=5, minutes=30))


def _get_public_url() -> Optional[str]:
    """Auto-detect ngrok URL from local ngrok API."""
    try:
        import requests as req
        resp = req.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if resp.status_code == 200:
            for tunnel in resp.json().get("tunnels", []):
                if tunnel.get("proto") == "https":
                    url = tunnel["public_url"].rstrip("/")
                    return url
    except Exception:
        pass
    return None


def _fire_reminder_sync(reminder_message: str, public_url: str) -> str:
    """
    Synchronous function that places a Twilio outbound call.
    This runs in a thread via asyncio.to_thread() to avoid blocking the event loop.

    Returns the call SID on success, or raises on failure.
    """
    from twilio.rest import Client
    from urllib.parse import urlencode

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    params = urlencode({"message": reminder_message})
    webhook_url = f"{public_url}/call/reminder?{params}"

    call = client.calls.create(
        to=settings.TWILIO_CALLBACK_NUMBER,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=webhook_url,
    )
    return call.sid


class ReminderScheduler:
    """Polls for due reminders and fires outbound calls."""

    def __init__(self, structured_store, poll_interval_seconds: int = 30):
        self._store = structured_store
        self._interval = poll_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def start(self):
        """Start the background polling loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"Reminder scheduler started (interval={self._interval}s)."
        )

    def stop(self):
        """Cancel the polling loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Reminder scheduler stopped.")

    async def _poll_loop(self):
        """Main polling coroutine."""
        while self._running:
            try:
                await self._check_reminders()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler poll error: {e}", exc_info=True)
            await asyncio.sleep(self._interval)

    async def _check_reminders(self):
        """Check for due reminders and fire them."""
        from app.memory.models import ReminderStatus

        active = await self._store.get_reminders(status=ReminderStatus.ACTIVE)
        if not active:
            return

        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(IST)
        logger.debug(f"Scheduler check: {len(active)} active reminder(s), now_utc={now_utc.isoformat()}, now_ist={now_ist.isoformat()}")

        for reminder in active:
            due = self._is_due(reminder.trigger_time, now_utc)
            if not due:
                continue

            logger.info(
                f"🔔 Reminder #{reminder.id} is DUE: '{reminder.message}' (trigger={reminder.trigger_time})"
            )

            # Pre-flight checks
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                logger.error("Twilio credentials not configured — cannot fire reminder.")
                await self._store.update_reminder_status(reminder.id, ReminderStatus.FIRED)
                continue

            if not settings.TWILIO_CALLBACK_NUMBER:
                logger.error("TWILIO_CALLBACK_NUMBER not set — don't know who to call.")
                await self._store.update_reminder_status(reminder.id, ReminderStatus.FIRED)
                continue

            public_url = _get_public_url()
            if not public_url:
                logger.error("No ngrok URL available — cannot deliver reminder call. Is ngrok running?")
                # Don't mark as fired so we retry next poll
                continue

            # Fire the call in a thread to avoid blocking the event loop
            try:
                call_sid = await asyncio.to_thread(
                    _fire_reminder_sync, reminder.message, public_url
                )
                logger.info(f"✅ Reminder #{reminder.id} call placed — SID: {call_sid}")
                await self._store.update_reminder_status(reminder.id, ReminderStatus.FIRED)
            except Exception as e:
                logger.error(f"❌ Failed to fire reminder #{reminder.id}: {e}", exc_info=True)
                # Mark as fired to prevent infinite retries
                await self._store.update_reminder_status(reminder.id, ReminderStatus.FIRED)

    @staticmethod
    def _is_due(trigger_time: str, now_utc: datetime) -> bool:
        """
        Parse trigger_time and check if it's in the past.

        The LLM is told to generate IST datetimes (since user is in India).
        We parse them as IST and compare against now_utc.
        """
        try:
            # Try full ISO formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
            ]:
                try:
                    dt = datetime.strptime(trigger_time, fmt)
                    # Assume naive datetimes are IST (user's timezone)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=IST)
                    return dt <= now_utc.astimezone(IST)
                except ValueError:
                    continue

            # Try with timezone info already embedded
            try:
                dt = datetime.fromisoformat(trigger_time)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=IST)
                return dt <= now_utc.astimezone(IST)
            except ValueError:
                pass

            # Try HH:MM — interpret as today IST
            if len(trigger_time) == 5 and ":" in trigger_time:
                h, m = map(int, trigger_time.split(":"))
                now_ist = now_utc.astimezone(IST)
                dt = now_ist.replace(hour=h, minute=m, second=0, microsecond=0)
                return dt <= now_ist

        except Exception as e:
            logger.warning(f"Could not parse trigger_time '{trigger_time}': {e}")

        return False
