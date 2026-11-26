import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.models import Message, ChatRequest, ChatResponse, Conversation
from app.services.websocket_manager import manager
from app.services.chat_service import (
    get_conversation,
    delete_conversation,
    process_chat_async
)
from app.services.provider_errors import ChatProviderError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.db.session import get_db_session, get_session_factory


SessionDep = Annotated[
    AsyncSession,
    Depends(get_db_session)
]


SessionFactoryDep = Annotated[
    async_sessionmaker[AsyncSession],
    Depends(get_session_factory),
]


router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "Welcome to the AI Chatbot API"
    }

@router.get("/healthcheck", tags=["Health"])
def healthcheck():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/info")
def info():
    return {
        "project": "AI Chatbot API",
        "version": "1.0.0",
        "framework": "FastAPI",
        "chatbot_type": "Rule-based"
    }


@router.get(
        "/conversations/{conversation_id}",
        response_model=Conversation,
)
async def get_conversation_history(
    conversation_id: str,
    db: SessionDep,
) -> Conversation:

    return await get_conversation(
        db,
        conversation_id,
    )


@router.delete(
        "/conversations/{conversation_id}",
        status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation_history(
    conversation_id:str,
    db: SessionDep
) -> None:

    await delete_conversation(
        db,
        conversation_id
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    payload: ChatRequest,
    db: SessionDep,
) -> ChatResponse:

    try:
        return await process_chat_async(
            payload,
            session=db,
        )

    except ChatProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.websocket("/ws/{client_id}")
async def websocket_chat(
    websocket: WebSocket,
    client_id: str,
    session_factory: SessionFactoryDep
) -> None:

    connected = await manager.connect(websocket, client_id)

    if not connected:
        return

    try:
        while True:
            try:
                # Wait for a message from the client
                data = await websocket.receive_json()

                # Validate using pydantic model
                payload = ChatRequest.model_validate(data)

                # process the message using our chat service
                async with session_factory() as db:
                    response = await process_chat_async(
                        payload,
                        session=db,
                    )

            except (ValidationError, json.JSONDecodeError):
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "detail": "Invalid chat message payload"
                    }
                )
                continue

            except HTTPException as exc:
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "status_code": exc.status_code,
                        "detail": exc.detail
                    }
                )
                continue

            except ChatProviderError as exc:
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "status_code": exc.status_code,
                        "code": exc.code,
                        "detail": exc.detail
                    }
                )
                continue

            #Serialize the Pydantic response to JSON-compatible data
            await manager.send_message(
                client_id,
                {
                    "type": "chat_response",
                    **response.model_dump(mode="json")
                }
            )

    except WebSocketDisconnect:
        pass

    finally:
        manager.disconnect(client_id, websocket)