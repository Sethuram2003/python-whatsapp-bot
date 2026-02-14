import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from app.dependencies import get_settings, verify_signature
from app.config import Settings
from app.core.WhatsApp import process_whatsapp_message, is_valid_whatsapp_message

router = APIRouter()

@router.get("")
async def webhook_verify(request: Request, settings: Settings = Depends(get_settings)):
    """
    WhatsApp webhook verification (GET request).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.verify_token:
            logging.info("WEBHOOK_VERIFIED")
            return int(challenge)
        else:
            logging.info("VERIFICATION_FAILED")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        logging.info("MISSING_PARAMETER")
        raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("")
async def webhook_post(
    payload: dict = Depends(verify_signature),  
    settings: Settings = Depends(get_settings)
):
    """
    Handle incoming WhatsApp messages and events.
    """
    if payload.get("entry") and payload["entry"][0].get("changes") and \
       payload["entry"][0]["changes"][0].get("value", {}).get("statuses"):
        logging.info("Received a WhatsApp status update.")
        return {"status": "ok"}

    if is_valid_whatsapp_message(payload):
        await process_whatsapp_message(payload, settings)  
        return {"status": "ok"}
    else:
        logging.info("Not a WhatsApp API event")
        raise HTTPException(status_code=404, detail="Not a WhatsApp API event")