import random
import hashlib
from django.core.cache import cache
from django.conf import settings
import hmac

OTP_EXPIRY = 60  # seconds


def hash_otp(phone, otp):
    message = f"{phone}:{otp}".encode()
    secret = settings.SECRET_KEY.encode()

    return hmac.new(
        secret,
        message,
        hashlib.sha256
    ).hexdigest()

def generate_and_store_otp(phone):
    otp = random.randint(100000, 999999)

    hashed_otp = hash_otp(phone, otp)

    cache.set(
        f"otp:{phone}",
        hashed_otp,
        timeout=OTP_EXPIRY
    )

    return otp

def verify_otp(phone, otp):
    stored_hash = cache.get(f"otp:{phone}")

    if not stored_hash:
        return False

    incoming_hash = hash_otp(phone, otp)

    if not hmac.compare_digest(stored_hash, incoming_hash):
        return False

    cache.delete(f"otp:{phone}")
    return True
