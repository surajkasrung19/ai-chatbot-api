
import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.orm_models import Base
from app.db.session import get_db_session, get_session_factory
from app.services import chat_service
from app.services.responders import RuleBasedResponder
from app.services.responder_factory import get_responder
from app.services.websocket_manager import manager


@pytest.fixture(autouse=True)
def mock_ai_provider(monkeypatch):
    # Automated tests never contact the real AI API.
    monkeypatch.setenv("CHATBOT_PROVIDER", "rule-based")
    get_responder.cache_clear()

    monkeypatch.setattr(
        chat_service,
        "get_responder",
        RuleBasedResponder,
    )

    manager.active_connections.clear()

    yield

    manager.active_connections.clear()
    get_responder.cache_clear()


@pytest.fixture
def db_factory(tmp_path):

    database_file = (tmp_path / "test.db").as_posix()
    database_url = f"sqlite+aiosqlite:///{database_file}"

    test_engine = create_async_engine(
        database_url,
        poolclass=NullPool,
    )

    async def setup_database():
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(setup_database())

    factory = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    yield factory

    asyncio.run(test_engine.dispose())


@pytest.fixture
def client(db_factory):

    async def override_get_db_session():
        async with db_factory() as session:
            yield session

    # REST endpoints use the temporary database
    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    # WebSocket messages use the same temporary database
    app.dependency_overrides[get_session_factory] = (
        lambda: db_factory
    )


    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(
            get_db_session, None
        )
        app.dependency_overrides.pop(
            get_session_factory, None
        )