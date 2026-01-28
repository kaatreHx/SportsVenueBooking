from twilio.rest import Client
from django.conf import settings

client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

from twilio.base.exceptions import TwilioRestException

def send_sms(phone, message):
    try:
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )
        return True, "SMS sent successfully"
    except TwilioRestException as e:
        return False, str(e)
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"
