import asyncio
import pytest
from fastapi import HTTPException

from app.models import ChatRequest, Message
from app.db.memory import conversations_db

from app.services.chat_service import (
    create_conversation,
    get_conversation,
    process_chat_async,
)

from app.utils.nlp_stub import(
    generate_stub_response,
    SAMPLE_RESPONSES,
    DEFAULT_RESPONSES,
)


def test_known_keyword_response():
    response = generate_stub_response(
        "Can you explain FASTAPI?"
    )

    assert response in SAMPLE_RESPONSES["fastapi"]


def test_unknown_keyword_response():
    response = generate_stub_response(
        "unrecognized-topic-98765"
    )

    assert response in DEFAULT_RESPONSES


def test_create_conversation():
    conversation = create_conversation()

    assert conversation.id in conversations_db
    assert conversation.messages == []


def test_missing_conversation():
    with pytest.raises(HTTPException) as exc_info:
        get_conversation("invalid-id")

    assert exc_info.value.status_code == 404


def test_process_chat_with_mocked_response():

    class FakeResponder:
        async def generate(
                self,
                message: str,
                history: list[Message]
        ) -> str:
            return "This is a mocked response"


    result = asyncio.run(
        process_chat_async(
            ChatRequest(message="Hello"),
            responder=FakeResponder()
        )
    )

    assert result.message.content == "This is a mocked response"
    assert result.conversation_id in conversations_db
    assert len(result.conversation_history) ==  2