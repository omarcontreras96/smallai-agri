"""Outgoing SMS via Africa's Talking. In the sandbox the webhook's HTTP response is not delivered
to the phone, so replies are sent through the SMS API from the shortcode.

Off unless AT_USERNAME and AT_API_KEY are set (env or .env.local); the local /inbox never needs it.
"""
import logging
import os
from pathlib import Path

log = logging.getLogger("uvicorn.error")
ENV_FILE = Path(__file__).resolve().parent.parent / ".env.local"
_sms = None


def load_env(path: Path = ENV_FILE) -> None:
    """Minimal KEY=VALUE reader; real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def enabled() -> bool:
    return bool(os.environ.get("AT_USERNAME") and os.environ.get("AT_API_KEY"))


def _client():
    global _sms
    if _sms is None:
        import africastalking
        africastalking.initialize(os.environ["AT_USERNAME"], os.environ["AT_API_KEY"])
        _sms = africastalking.SMS
    return _sms


def send(phone: str, text: str, shortcode: str | None = None) -> None:
    """Send one reply; failures are logged, never raised (the webhook must still answer 200)."""
    sender = os.environ.get("AT_SHORTCODE") or shortcode
    try:
        res = _client().send(text, [phone], sender_id=sender)
        log.info("AT send to %s: %s", phone[-4:], res.get("SMSMessageData", {}).get("Message"))
    except Exception as e:
        log.warning("AT send to %s failed: %s", phone[-4:], e)
