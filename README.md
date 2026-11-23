# AI Chatbot API — FastAPI


[![Chatbot API Tests](https://github.com/surajkasrung19/ai-chatbot-api/actions/workflows/tests.yml/badge.svg)](https://github.com/surajkasrung19/ai-chatbot-api/actions/workflows/tests.yml)


A Python backend chatbot project built with **FastAPI**, featuring REST APIs, real-time **WebSocket** chat, validated requests, and in-memory conversation management. The chatbot currently generates **rule-based responses**; it does **not** use a large language model yet.

## Features

- Chat through `POST /chat` and `WS /ws/{client_id}`.
- Start a new conversation or continue one by its conversation ID.
- Retrieve and delete conversation history.
- Validate incoming chat requests with Pydantic.
- Process chat requests through an asynchronous API layer.
- Run automated model, service, API, and WebSocket tests with pytest.
- Run in Docker with a container health check.

## Tech stack

| Category | Technology |
| --- | --- |
| Language | Python 3.13 |
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| Data validation | Pydantic |
| Real-time communication | WebSockets |
| Tests | pytest, FastAPI TestClient |
| Containerization | Docker, Docker Compose |
| Conversation storage | In-memory Python dictionary |

## Project structure

```text
ai_chatbot_api/
├── app/
│   ├── main.py                 # FastAPI app and router registration
│   ├── routes.py               # REST and WebSocket endpoints
│   ├── models.py               # Pydantic request/response models
│   ├── db/                     # In-memory conversation storage
│   ├── services/               # Chat logic and WebSocket manager
│   └── utils/                  # Rule-based response generation
├── scripts/
│   └── websocket_client.py     # Example WebSocket client
├── tests/                      # Automated tests and fixtures
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Quick start with Docker

**Prerequisite:** Docker Desktop running with Linux containers.

From the project root:

```bash
docker compose up --build -d
docker compose ps
```

Open the interactive REST API documentation at **http://127.0.0.1:8000/docs**.

Check the application:

```bash
docker compose logs --tail=50 chatbot-api
```

Stop the container:

```bash
docker compose down
```

> Docker Compose publishes the API on `127.0.0.1:8000` for local development. The container's health check probes `GET /healthcheck`.

## Run locally without Docker

**Prerequisite:** Python 3.13 installed.

On Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Visit **http://127.0.0.1:8000/docs**.

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Welcome response |
| `GET` | `/healthcheck` | Health status and timestamp |
| `GET` | `/info` | Application information |
| `POST` | `/chat` | Send a message; optionally continue a conversation |
| `GET` | `/conversations/{conversation_id}` | Retrieve stored conversation |
| `DELETE` | `/conversations/{conversation_id}` | Delete stored conversation (`204 No Content`) |
| `WebSocket` | `/ws/{client_id}` | Real-time chat |

### Chat request

Send `POST /chat` with JSON:

```json
{
  "message": "What is Python?"
}
```

The response contains the assistant's `message`, a generated `conversation_id`, and `conversation_history`. To continue the same chat, send another request with the returned conversation ID:

```json
{
  "message": "Tell me about FastAPI",
  "conversation_id": "<conversation-id-from-previous-response>"
}
```

Blank or whitespace-only messages are rejected by request validation. Unknown conversation IDs return `404 Not Found`.

### PowerShell request example

```powershell
$body = @{ message = "Hello" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method Post -ContentType "application/json" -Body $body
```

### WebSocket example

When the API is running and the virtual environment has the required dependencies:

```powershell
python scripts/websocket_client.py
```

This client connects to `ws://127.0.0.1:8000/ws/client-1` and demonstrates chat messages and conversation history.

> WebSocket endpoints do not appear in Swagger UI's OpenAPI endpoint list.

## Automated testing

Run from the project root with the virtual environment active:

```bash
python -m pytest -v
```

For statement coverage:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

The test suite exercises model validation, chatbot services, REST endpoints, conversation deletion, and WebSocket messaging.

## Architecture overview

```text
REST client / WebSocket client
             |
             v
      FastAPI routes
             |
             v
        Chat service
        /          \
Rule-based NLP   Conversation store
                     (in memory)
```

## Current limitations

- **No persistence:** Conversations are held in process memory and are lost when the service restarts or a container is recreated.
- **Rule-based replies:** This is not yet an LLM-powered chatbot.
- **Development-focused security:** Authentication, authorization, rate limiting, and production security hardening are not implemented.
- **Container image scanning:** The Python base image / dependencies can have outstanding vulnerability findings; review and remediate them before a public deployment.

## Future improvements

- PostgreSQL-backed conversation persistence.
- Authentication and per-user conversation ownership.
- Optional LLM integration with securely managed API keys.
- Rate limiting, observability, and improved production container hardening.

## Project status

Learning project: core REST, WebSocket, automated testing, and Docker workflows have been implemented and tested locally. Production deployment is **not** currently included.