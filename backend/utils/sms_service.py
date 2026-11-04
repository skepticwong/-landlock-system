"""
SMS service abstraction with mock and Africa's Talking placeholder.

Usage:
  from config import config
  from utils.sms_service import send_sms
  send_sms(phone, message)
"""
from typing import List
from config import config as cfg  # use project's config
import re

try:
    # allow optional africastalking usage if installed
    import africastalking
except Exception:
    africastalking = None


def _normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+").strip()
    if cleaned.startswith('+265'):
        return '0' + cleaned[4:]
    if cleaned.startswith('265'):
        return '0' + cleaned[3:]
    return cleaned


def send_sms(phone: str, message: str) -> bool:
    """Send a single SMS using configured provider. Returns True on success."""
    phone = _normalize_phone(phone)

    mode = getattr(cfg, 'SMS_MODE', 'mock')
    if mode == 'mock' or africastalking is None:
        print(f"[SMS MOCK] To: {phone}")
        print(message)
        print("[SMS MOCK] ---")
        return True

    if mode == 'africastalking':
        # real provider path (requires africastalking library and config)
        try:
            africastalking.initialize(cfg.AFRICAS_TALKING_USERNAME, cfg.AFRICAS_TALKING_API_KEY)
            sms = africastalking.SMS
            response = sms.send(message, [phone])
            return response is not None
        except Exception as e:
            print(f"[SMS ERROR] {e}")
            return False

    # Unsupported mode: fallback to mock
    print(f"[SMS FALLBACK-MOCK] mode={mode} To: {phone}")
    print(message)
    return True


def send_bulk(phones: List[str], message: str) -> dict:
    results = {p: send_sms(p, message) for p in phones}
    return results
