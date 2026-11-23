import pytest
from pydantic import ValidationError

from app.models import ChatRequest



def test_valid_chat_request():
    request = ChatRequest(message="Hello Python")

    assert request.message == "Hello Python"
    assert request.conversation_id is None


def test_message_whitespace_is_removed():
    request = ChatRequest(message="   Hello   ")

    assert request.message == "Hello"


@pytest.mark.parametrize(
    "message",
    ["", "   ","\n\t"]
)
def test_empty_messages_are_rejected(message):
    with pytest.raises(ValidationError):
        ChatRequest(message=message)

