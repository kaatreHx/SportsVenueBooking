import threading
from django.conf import settings


def send_sms(phone, message):
    """Send SMS via Twilio. Runs in a background thread to avoid blocking."""
    def _send():
        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException

            client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
            )
            print(f"[SMS] Sent to {phone}")
        except Exception as e:
            # Log but never crash — registration must succeed regardless
            print(f"[SMS] Failed to send to {phone}: {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    return True, "SMS queued"
