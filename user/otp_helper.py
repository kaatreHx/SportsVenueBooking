import random
import hashlib
import hmac
from django.conf import settings

OTP_EXPIRY = 300  # 5 minutes


def _get_cache():
    """Return cache backend, falling back to local memory if Redis is down."""
    try:
        from django.core.cache import cache
        # Quick connectivity check
        cache.set('_ping', '1', timeout=1)
        return cache
    except Exception:
        from django.core.cache import caches
        try:
            return caches['locmem']
        except Exception:
            from django.core.cache import cache
            return cache


def hash_otp(phone, otp):
    message = f"{phone}:{otp}".encode()
    secret = settings.SECRET_KEY.encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def generate_and_store_otp(phone):
    otp = random.randint(100000, 999999)
    hashed_otp = hash_otp(phone, otp)
    cache = _get_cache()
    cache.set(f"otp:{phone}", hashed_otp, timeout=OTP_EXPIRY)
    return otp


def verify_otp(phone, otp):
    cache = _get_cache()
    stored_hash = cache.get(f"otp:{phone}")

    if not stored_hash:
        return False

    incoming_hash = hash_otp(phone, str(otp))

    if not hmac.compare_digest(stored_hash, incoming_hash):
        return False

    cache.delete(f"otp:{phone}")
    return True
