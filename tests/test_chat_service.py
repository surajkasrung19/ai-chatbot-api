
import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import ChatRequest, Message
from app.services.chat_service import (
    get_conversation,
    process_chat_async,
)
from app.utils.nlp_stub import (
    generate_stub_response,
    SAMPLE_RESPONSES,
    DEFAULT_RESPONSES,
)
from app.db.orm_models import ConversationORM


class FakeResponder:
    async def generate(
        self,
        message: str,
        history: list[Message],
    ) -> str:
        return "Mocked AI response"


class FailingResponder:
    async def generate(
        self,
        message: str,
        history: list[Message],
    ) -> str:
        raise RuntimeError("AI unavailable")


def test_known_keyword_response():
    response = generate_stub_response("Explain FastAPI")
    assert response in SAMPLE_RESPONSES["fastapi"]


def test_unknown_keyword_response():
    response = generate_stub_response("unknown-topic-123")
    assert response in DEFAULT_RESPONSES


def test_missing_conversation(db_factory):

    async def scenario():
        async with db_factory() as session:
            with pytest.raises(HTTPException) as exc:
                await get_conversation(session, "missing-id")

            assert exc.value.status_code == 404

    asyncio.run(scenario())


def test_process_chat_saves_messages(db_factory):

    async def scenario():
        async with db_factory() as session:

            result = await process_chat_async(
                ChatRequest(message="Hello"),
                session=session,
                responder=FakeResponder(),
            )

            assert result.message.content == "Mocked AI response"
            assert len(result.conversation_history) == 2

            saved = await get_conversation(
                session, result.conversation_id
            )

            assert len(saved.messages) == 2
            assert saved.messages[0].role == "user"
            assert saved.messages[1].role == "assistant"

    asyncio.run(scenario())


def test_failed_provider_preserves_history(db_factory):

    async def scenario():
        async with db_factory() as session:

            first = await process_chat_async(
                ChatRequest(message="Hello"),
                session=session,
                responder=FakeResponder(),
            )

            original = await get_conversation(
                session, first.conversation_id
            )

            with pytest.raises(
                RuntimeError, match="AI unavailable"
            ):
                await process_chat_async(
                    ChatRequest(
                        message="Explain Python",
                        conversation_id=first.conversation_id,
                    ),
                    session=session,
                    responder=FailingResponder(),
                )

            saved = await get_conversation(
                session, first.conversation_id
            )

            assert saved.messages == original.messages
            assert len(saved.messages) == 2

    asyncio.run(scenario())


def test_failed_provider_does_not_create_conversation(db_factory):

    async def scenario():
        async with db_factory() as session:

            with pytest.raises(RuntimeError):
                await process_chat_async(
                    ChatRequest(message="Hello"),
                    session=session,
                    responder=FailingResponder(),
                )

            count = await session.scalar(
                select(func.count())
                .select_from(ConversationORM)
            )

            assert count == 0

    asyncio.run(scenario())
