from app.models import Message
from app.services import chat_service
from app.services.provider_errors import ChatProviderError


def test_create_chat(client):
    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )

    assert response.status_code == 200

    data = response.json()

    assert "conversation_id" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["conversation_history"]) == 2

def test_continue_conversation(client):
    first_response = client.post(
        "/chat",
        json={"message": "Hello"}
    )

    conversation_id = first_response.json()["conversation_id"]

    second_response = client.post(
        "/chat",
        json={
            "message": "Tell me about python",
            "conversation_id": conversation_id
        }
    )

    assert second_response.status_code == 200

    data = second_response.json()

    assert data["conversation_id"] == conversation_id
    assert len(data["conversation_history"]) == 4


def test_invalid_message(client):
    response = client.post(
        "/chat",
        json={"message": "   "}
    )

    assert response.status_code == 422


def test_nonexistent_conversation(client):
    response = client.post(
        "/chat",
        json={
            "message": "Hello",
            "conversation_id": "invalid-123"
        }
    )

    assert response.status_code == 404


def test_delete_conversation(client):

    # Create conversation
    create_response = client.post(
        "/chat",
        json={"message": "Hello"}
    )

    conversation_id = create_response.json()["conversation_id"]

    # Delete conversation
    delete_response = client.delete(
        f"/conversations/{conversation_id}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    # Confirm the conversation no longer exists
    get_response = client.get(
        f"/conversations/{conversation_id}"
    )

    assert get_response.status_code == 404


def test_delete_unknown_conversation(client):
    # Arrange
    invalid_id = "unknown-123"

    # Act
    response = client.delete(
        f"/conversations/{invalid_id}"
    )

    # Assert
    assert response.status_code == 404

    assert "not found" in response.json()["detail"].lower()


def test_info(client):
    response = client.get(
        "/info"
    )

    assert response.status_code  == 200


def test_chat_provider_unavailable(client, monkeypatch):

    class FailingResponder:
        async def generate(
                self,
                message: str,
                history: list[Message]
        ) -> str:
            raise ChatProviderError(
                detail="AI service is temporarily unavailable.",
                status_code=503,
                code="connection_error"
            )

    monkeypatch.setattr(
        chat_service,
        "get_responder",
        lambda: FailingResponder()
    )

    response = client.post(
        "/chat",
        json={"message": "Explain FastAPI"}
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "AI service is temporarily unavailable."
    }



def test_conversation_is_saved_in_database(client):

    create_response = client.post(
        "/chat",
        json={"message": "Hello"}
    )

    assert create_response.status_code == 200

    conversation_id = (
        create_response.json()["conversation_id"]
    )

    get_response = client.get(
        f"/conversations/{conversation_id}"
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == conversation_id
    assert len(data["messages"]) == 2

    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"