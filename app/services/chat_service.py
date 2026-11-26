
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ChatRequest,
    ChatResponse,
    Conversation,
    Message,
)
from app.db import conversation_repository as repository
from app.services.responders import ChatResponder
from app.services.responder_factory import get_responder
from app.services.provider_errors import ChatProviderError


async def get_conversation(
    session: AsyncSession,
    conversation_id: str,
) -> Conversation:

    record = await repository.find_conversation(
        session, conversation_id
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )

    return repository.to_schema(record)


async def delete_conversation(
    session: AsyncSession,
    conversation_id: str,
) -> None:

    deleted = await repository.delete_conversation(
        session, conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )


async def process_chat_async(
    payload: ChatRequest,
    session: AsyncSession,
    responder: ChatResponder | None = None,
) -> ChatResponse:

    # Load previous history, if provided.
    if payload.conversation_id is None:
        history = []

    else:
        conversation = await get_conversation(
            session, payload.conversation_id
        )

        history = conversation.messages.copy()

        # End the read transaction before external AI I/O.
        await session.rollback()

    engine = (
        responder
        if responder is not None
        else get_responder()
    )

    # Do not write to the database yet.
    bot_reply = await engine.generate(
        message=payload.message,
        history=history,
    )

    if not isinstance(bot_reply, str) or not bot_reply.strip():
        raise ChatProviderError(
            detail="AI provider returned an empty response.",
            status_code=502,
            code="empty_response",
        )

    now = datetime.now(timezone.utc)

    user_message = Message(
        id=str(uuid4()),
        role="user",
        content=payload.message,
        created_at=now,
    )

    assistant_message = Message(
        id=str(uuid4()),
        role="assistant",
        content=bot_reply,
        created_at=datetime.now(timezone.utc),
    )

    try:
        saved = await repository.save_exchange(
            session=session,
            conversation_id=payload.conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation no longer exists",
        ) from exc

    return ChatResponse(
        message=assistant_message,
        conversation_id=saved.id,
        conversation_history=saved.messages,
    )
