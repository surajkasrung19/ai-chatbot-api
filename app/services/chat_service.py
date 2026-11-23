import asyncio
from datetime import datetime, timezone
from uuid import uuid4


from fastapi import HTTPException

from app.db.memory import conversations_db
from app.utils.nlp_stub import generate_stub_response

from app.models import (
    ChatRequest,
    ChatResponse,
    Conversation,
    Message,
)


def generate_bot_response(user_message: str) -> str:
    response = generate_stub_response(user_message)
    return response


def get_conversation(conversation_id: str) -> Conversation:
    conversation = conversations_db.get(conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    return conversation

def create_conversation() -> Conversation:
    now = datetime.now(timezone.utc)

    conversation = Conversation(
        id=str(uuid4()),
        created_at=now,
        updated_at=now
    )

    conversations_db[conversation.id] = conversation

    return conversation


def process_chat(payload: ChatRequest) -> ChatResponse:

    # Find an existing conversation or create a new one
    if payload.conversation_id is None:
        conversation = create_conversation()
    else:
        conversation = get_conversation(payload.conversation_id)

    now = datetime.now(timezone.utc)

    # Create user message
    user_message = Message(
        id=str(uuid4()),
        role="user",
        content=payload.message,
        created_at=now
    )

    # Generate assistant response using stage 3 logic
    bot_reply = generate_bot_response(payload.message)

    assistant_message = Message(
        id=str(uuid4()),
        role="assistant",
        content=bot_reply,
        created_at=datetime.now(timezone.utc)
    )

    # Save both messages to the conversation
    conversation.messages.extend([
        user_message,
        assistant_message
    ])

    conversation.updated_at = datetime.now(timezone.utc)

    return ChatResponse(
        message=assistant_message,
        conversation_id=conversation.id,
        conversation_history=conversation.messages.copy()
    )


def delete_conversation(conversation_id: str) -> None:

    get_conversation(conversation_id)

    del conversations_db[conversation_id]


async def process_chat_async(payload: ChatRequest) -> ChatResponse:

    # Simulate waiting for an external AI service
    await asyncio.sleep(0.3)

    return process_chat(payload)