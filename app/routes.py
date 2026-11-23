import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.models import Message, ChatRequest, ChatResponse, Conversation
from app.services.websocket_manager import manager
from app.services.chat_service import (
    process_chat,
    get_conversation,
    delete_conversation,
    process_chat_async
)


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
    response_model=Conversation
)
def get_conversation_history(conversation_id: str) -> Conversation:
    return get_conversation(conversation_id)

@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation_history(conversation_id: str) -> None:
    delete_conversation(conversation_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    return await process_chat_async(payload)


@router.websocket("/ws/{client_id}")
async def websocket_chat(
    websocket: WebSocket,
    client_id: str
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
                response = await process_chat_async(payload)

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