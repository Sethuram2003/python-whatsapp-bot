from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class Profile(BaseModel):
    name: str

class Contact(BaseModel):
    wa_id: str
    profile: Profile

class TextMessage(BaseModel):
    body: str

class Message(BaseModel):
    from_: str  # sender's phone number
    id: str
    timestamp: str
    text: Optional[TextMessage] = None
    type: str

class ChangeValue(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: List[Contact]
    messages: Optional[List[Message]] = None
    statuses: Optional[List[Any]] = None

class Change(BaseModel):
    value: ChangeValue
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WebhookPayload(BaseModel):
    object: str
    entry: List[Entry]