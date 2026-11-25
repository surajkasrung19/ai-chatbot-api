
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.memory import conversations_db
from app.services.websocket_manager import manager

from app.services import chat_service
from app.services.responders import RuleBasedResponder
from app.services.responder_factory import get_responder


@pytest.fixture(autouse=True)
def reset_test_state(monkeypatch):

    # Force a non-billable provider during automated tests
    monkeypatch.setenv(
        "CHATBOT_PROVIDER",
        "rule-based"
    )

    # Clear any previously cached provider
    get_responder.cache_clear()

    # Replace the factory reference used by chat_service
    # so tests never invoke an external AI API
    monkeypatch.setattr(
        chat_service,
        "get_responder",
        RuleBasedResponder
    )

    # Reset shared application state
    conversations_db.clear()
    manager.active_connections.clear()

    yield

    # Cleanup after each test
    conversations_db.clear()
    manager.active_connections.clear()
    get_responder.cache_clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client