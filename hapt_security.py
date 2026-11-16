import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_SECRET = os.getenv("HAPT_WEBHOOK_SECRET", "HaptInvestSecureHMAC2026!")

def verify_telegram_hmac(request_body: bytes, provided_signature: str) -> bool:
    """
    Cryptographically verifies incoming webhook payloads using HMAC-SHA256
    to guarantee message integrity and authenticity.
    """
    if not provided_signature:
        return False
    
    computed_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, provided_signature)