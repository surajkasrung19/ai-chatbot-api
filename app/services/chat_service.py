import asyncio
from datetime import datetime, timezone
from uuid import uuid4


from fastapi import HTTPException
from app.services.responders import ChatResponder
from app.services.responder_factory import get_responder

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


def delete_conversation(conversation_id: str) -> None:

    get_conversation(conversation_id)

    del conversations_db[conversation_id]



async def process_chat_async(
    payload: ChatRequest,
    responder: ChatResponder | None = None
) -> ChatResponse:

    if payload.conversation_id is None:
        conversation = None
        history = []
    else:
        conversation = get_conversation(
            payload.conversation_id
        )
        history = conversation.messages.copy()

    # Use the injected provider or the configured default
    engine = responder if responder is not None else get_responder()

    # Generate the reply before modifying conversation state
    bot_reply = await engine.generate(
        message=payload.message,
        history=history
    )

    if not isinstance(bot_reply, str) or not bot_reply.strip():
        raise RuntimeError("Invalid chatbot response")

    # Only create a new conversation after generation succeeds
    if conversation is None:
        conversation = create_conversation()

    now = datetime.now(timezone.utc)

    user_message = Message(
        id=str(uuid4()),
        role="user",
        content=payload.message,
        created_at=now
    )

    assistant_message = Message(
        id=str(uuid4()),
        role="assistant",
        content=bot_reply,
        created_at=datetime.now(timezone.utc)
    )

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