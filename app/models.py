from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None

    @field_validator('message')
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Message cannot be empty or consist only whitespace."
            )

        return cleaned


class ChatResponse(BaseModel):
    message: Message
    conversation_id: str
    conversation_history: list[Message]

class Conversation(BaseModel):
    id: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime