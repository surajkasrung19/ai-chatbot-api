import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.memory import conversations_db
from app.services.websocket_manager import manager

@pytest.fixture(autouse=True)
def reset_test_state():
    # Clean shared in-memory state before each test
    conversations_db.clear()
    manager.active_connections.clear()

    yield

    # Clean up after the test
    conversations_db.clear()
    manager.active_connections.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

