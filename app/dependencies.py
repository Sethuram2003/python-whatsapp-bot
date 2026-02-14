import hashlib
import hmac
import logging
from fastapi import Request, HTTPException, Depends
from app.config import Settings
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()

async def verify_signature(request: Request, settings: Settings = Depends(get_settings)):
    """
    Dependency to verify X-Hub-Signature-256 header.
    Raises HTTP 403 if signature mismatch.
    """
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        logging.info("Missing signature header")
        raise HTTPException(status_code=403, detail="Missing signature")

    if not signature_header.startswith("sha256="):
        logging.info("Invalid signature format")
        raise HTTPException(status_code=403, detail="Invalid signature format")

    received_signature = signature_header[7:]  

    body = await request.body()
    payload = body.decode("utf-8")

    expected_signature = hmac.new(
        key=bytes(settings.app_secret, "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        logging.info("Signature verification failed")
        raise HTTPException(status_code=403, detail="Invalid signature")

    return await request.json()