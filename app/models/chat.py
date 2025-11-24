# app/models/chat.py

from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    source: Optional[str] = None   # e.g. "github", "linkedin", "demo"


class ChatResponse(BaseModel):
    reply: str
    state: Any                     # serialized State object
