from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="AI Chatbot API",
    description="A Chatbot backend built using FastAPI",
    version="1.0.0"
)

app.include_router(router)
