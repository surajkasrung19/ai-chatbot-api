
from app.services.websocket_manager import manager


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
