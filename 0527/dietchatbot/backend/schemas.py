from datetime import datetime
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    reply: str
    intent: str


class RecordCreate(BaseModel):
    session_id: str
    user_message: str
    recipe_reply: str
    intent: str


class RecordResponse(RecordCreate):
    id: int
    created_at: datetime
