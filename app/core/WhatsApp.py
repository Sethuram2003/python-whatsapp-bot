import logging
import json
import requests
import re
from app.core.LangAgent import chat_agent
from app.config import Settings

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def send_message(data, settings: Settings):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {settings.access_token}",
    }
    url = f"https://graph.facebook.com/{settings.version}/{settings.phone_number_id}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return {"status": "error", "message": "Request timed out"}, 408
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
        return {"status": "error", "message": "Failed to send message"}, 500
    else:
        log_http_response(response)
        return response

def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()

    # Convert **bold** to *bold* (WhatsApp uses single asterisks)
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text

async def process_whatsapp_message(body, settings: Settings):
    """
    Process incoming message, generate response, and send back.
    This function is called from the webhook route.
    """
    # Extract info
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    config = {
            "configurable": {
                "thread_id": f"{name}_{wa_id}"  
            }
        }

    agent = await chat_agent()

    response = await agent.ainvoke({
        "messages": [
            {"role": "user", "content": message_body}
        ]
    }, config)

    response = process_text_for_whatsapp(response["messages"][-1].content)

    data = get_text_message_input(settings.recipient_waid, response)
    send_message(data, settings)

def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )