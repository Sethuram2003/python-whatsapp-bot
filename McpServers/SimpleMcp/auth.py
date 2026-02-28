from fastapi import Header, HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

EXPECTED_API_KEY = os.getenv("API_KEY", "change-me-in-production")

async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Dependency that checks the X-API-Key header against the expected value.
    Raises HTTP 403 if the key is missing or invalid.
    """
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return x_api_key