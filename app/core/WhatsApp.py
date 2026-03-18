import logging
import json
import re
import base64
import httpx
import requests

from app.core.LangAgent import chat_agent, image_summarization_agent
from app.core.config import Settings

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    })

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
    text = re.sub(r"\【.*?\】", "", text).strip()
    # Convert **bold** to *bold*
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    return text


async def download_media(media_id: str, settings: Settings) -> str:
    """
    Download media from WhatsApp using the media ID.
    Returns the path to the downloaded file (temporary, but moved later).
    """
    media_url = f"https://graph.facebook.com/{settings.version}/{media_id}"
    headers = {"Authorization": f"Bearer {settings.access_token}"}
    print(f"Fetching media URL from: {media_url}")

    async with httpx.AsyncClient() as client:

        resp = await client.get(media_url, headers=headers)
        print(f"Media info response status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        download_url = data["url"]
        print(f"Download URL obtained: {download_url}")

        img_resp = await client.get(download_url, headers=headers)
        print(f"Image download status: {img_resp.status_code}")
        img_resp.raise_for_status()
        image_content = img_resp.content
        print(f"Downloaded {len(image_content)} bytes")

        try:
            image_agent = await image_summarization_agent()
            base64_image = base64.b64encode(image_content).decode('utf-8')
            mime_type = data.get("mime_type", "image/jpeg")

            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here is an image I received. Please provide a concise summary of its contents."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                    }
                ]
            }

            summary_response = await image_agent.ainvoke({
                "messages": [user_message]
            })
            summary = summary_response["messages"][-1].content
            print(f"Image summary: {summary}")
        except Exception as e:
            print(f"Image summarisation failed: {e}")


    return summary

async def process_whatsapp_message(body, settings: Settings):
    """
    Process incoming message, generate response, and send back.
    """
    print("Received message body:", json.dumps(body, indent=2))

    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_type = message.get("type")

    if message_type == "text":
        message_body = message["text"]["body"]

    elif message_type == "image":
        media_id = message["image"]["id"]
        caption = message["image"].get("caption", "")
        print(f"Image received. Media ID: {media_id}, Caption: {caption}")

        summary = None
        try:
            summary = await download_media(media_id, settings)
        except Exception as e:
            print(f"Image processing failed: {e}")
            summary = "Image summary could not be generated."

        if caption:
            message_body = f"{name} sent an image with caption: {caption}\nImage summary: {summary}"
        else:
            message_body = f"{name} sent an image (no caption)\nImage summary: {summary}"

    else:
        logging.warning(f"Unsupported message type: {message_type}")
        message_body = f"{name} sent a {message_type} message, which I cannot process. I can only handle text and images."

    config = {"configurable": {"thread_id": f"{name}_{wa_id}"}}
    agent = await chat_agent()
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": message_body}]},
        config
    )
    reply = process_text_for_whatsapp(response["messages"][-1].content)

    data = get_text_message_input(wa_id, reply)
    send_message(data, settings)

def is_valid_whatsapp_message(body):
    """Check if the incoming webhook has a valid message."""
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )