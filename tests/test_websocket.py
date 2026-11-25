
from app.services.websocket_manager import manager
from app.models import Message
from app.services import chat_service
from app.db.memory import conversations_db
from app.services.provider_errors import ChatProviderError


def test_websocket_conversation(client):

    with client.websocket_connect("/ws/test-client") as ws:

        # First message
        ws.send_json({"message": "Hello"})

        first = ws.receive_json()

        assert first["type"] == "chat_response"
        assert len(first["conversation_history"]) == 2

        conversation_id = first["conversation_id"]

        # Continue conversation
        ws.send_json({
            "message": "Explain Python",
            "conversation_id": conversation_id
        })

        second = ws.receive_json()

        assert second["type"] == "chat_response"
        assert second["conversation_id"] == conversation_id
        assert len(second["conversation_history"]) == 4

    # The WebSocket context has closed
    assert manager.active_connections == {}



def test_websocket_invalid_conversation(client):

    with client.websocket_connect("/ws/test-errors") as ws:

        ws.send_json({
            "message": "Hello",
            "conversation_id": "invalid-123"
        })

        response = ws.receive_json()

        assert response["type"] == "error"
        assert response["status_code"] == 404

        # Confirm the connection still works
        ws.send_json({"message": "Hello again"})

        valid_response = ws.receive_json()

        assert valid_response["type"] == "chat_response"
        assert len(valid_response["conversation_history"]) == 2

def test_websocket_recovers_after_provider_failure(
    client,
    monkeypatch
):

    # Arrange: Fake provider fails on the first request
    # and succeeds on the second request
    class FakeResponder:
        def __init__(self):
            self.call_count = 0


        async def generate(
            self,
            message: str,
            history: list[Message]
        ) -> str:

            self.call_count += 1

            if self.call_count == 1:
                raise ChatProviderError(
                    detail="AI temporarily unavailable",
                    status_code=503,
                    code="provider_unavailable"
                )

            return "AI is working again"

    responder = FakeResponder()

    # Inject the same fake responder for each request
    monkeypatch.setattr(
        chat_service,
        "get_responder",
        lambda: responder
    )

    with client.websocket_connect("/ws/recovery-client") as ws:

        # First request: provider failure
        ws.send_json({
            "message": "Hello"
        })

        first = ws.receive_json()

        assert first["type"] == "error"
        assert first["status_code"] == 503
        assert first["code"] == "provider_unavailable"

        # Failed new conversations should not be stored
        assert len(conversations_db) == 0

        # Second request: same WebSocket connection
        ws.send_json({
            "message": "Hello again"
        })

        second = ws.receive_json()

        assert second["type"] == "chat_response"
        assert second["message"]["content"] == (
            "AI is working again"
        )

        assert len(second["conversation_history"]) == 2

        conversation_id = second["conversation_id"]

        assert conversation_id in conversations_db
        assert responder.call_count == 2