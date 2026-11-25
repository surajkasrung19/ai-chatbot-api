from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.routes import router
from app.services.responder_factory import get_responder
from app.services.openai_responder import OpenAIResponder

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        # Only inspect the factory if a responder was cached.
        if get_responder.cache_info().currsize:
            responder = get_responder()

            if isinstance(responder, OpenAIResponder):
                await responder.client.close()

        get_responder.cache_clear()


app = FastAPI(
    title="AI Chatbot API",
    description="A Chatbot backend built using FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)
