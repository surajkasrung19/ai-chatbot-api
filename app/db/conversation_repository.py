
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.orm_models import ConversationORM, MessageORM
from app.models import Conversation, Message


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def to_schema(record: ConversationORM) -> Conversation:
    return Conversation(
        id=record.id,
        created_at=ensure_utc(record.created_at),
        updated_at=ensure_utc(record.updated_at),
        messages=[
            Message(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=ensure_utc(message.created_at),
            )
            for message in record.messages
        ],
    )


async def find_conversation(
    session: AsyncSession,
    conversation_id: str,
    lock: bool = False,
) -> ConversationORM | None:

    statement = (
        select(ConversationORM)
        .options(selectinload(ConversationORM.messages))
        .where(ConversationORM.id == conversation_id)
    )

    # Add row-level locking
    if lock:
        statement = statement.with_for_update(
            of=ConversationORM
        )

    return await session.scalar(statement)


async def save_exchange(
    session: AsyncSession,
    conversation_id: str | None,
    user_message: Message,
    assistant_message: Message,
) -> Conversation:

    async with session.begin():

        if conversation_id is None:
            now = datetime.now(timezone.utc)

            conversation = ConversationORM(
                id=str(uuid4()),
                created_at=now,
                updated_at=now,
                messages=[],
            )
            session.add(conversation)

        else:
            conversation = await find_conversation(
                session,
                conversation_id,
                lock=True
            )

            if conversation is None:
                raise ValueError("Conversation no longer exists")

        last_sequence = max(
            (item.sequence for item in conversation.messages),
            default=0,
        )

        conversation.messages.extend([
            MessageORM(
                id=user_message.id,
                conversation_id=conversation.id,
                role="user",
                content=user_message.content,
                created_at=user_message.created_at,
                sequence=last_sequence + 1,
            ),
            MessageORM(
                id=assistant_message.id,
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_message.content,
                created_at=assistant_message.created_at,
                sequence=last_sequence + 2,
            ),
        ])

        conversation.updated_at = datetime.now(timezone.utc)

    # The transaction has committed successfully.
    return to_schema(conversation)


async def delete_conversation(
    session: AsyncSession,
    conversation_id: str,
) -> bool:

    async with session.begin():
        conversation = await find_conversation(
            session,
            conversation_id,
            lock=True
        )

        if conversation is None:
            return False

        await session.delete(conversation)

    return True