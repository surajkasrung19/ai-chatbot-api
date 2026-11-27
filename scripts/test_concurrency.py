
import asyncio
import httpx


BASE_URL = "http://127.0.0.1:8000"


async def main():
    async with httpx.AsyncClient(timeout=30) as client:

        # First, create a conversation.
        first = await client.post(
            f"{BASE_URL}/chat",
            json={"message": "Hello"},
        )
        first.raise_for_status()

        conversation_id = first.json()["conversation_id"]

        # Send two requests to the same conversation
        # concurrently.
        responses = await asyncio.gather(
            client.post(
                f"{BASE_URL}/chat",
                json={
                    "message": "Explain Python",
                    "conversation_id": conversation_id,
                },
            ),
            client.post(
                f"{BASE_URL}/chat",
                json={
                    "message": "Explain FastAPI",
                    "conversation_id": conversation_id,
                },
            ),
        )

        print(
            "HTTP statuses:",
            [response.status_code for response in responses]
        )

        for response in responses:
            response.raise_for_status()

        # Read the final persisted conversation.
        saved = await client.get(
            f"{BASE_URL}/conversations/{conversation_id}"
        )
        saved.raise_for_status()

        messages = saved.json()["messages"]

        print("Stored messages:", len(messages))

        for message in messages:
            print(message["role"], ":", message["content"])

        assert len(messages) == 6
        print("Concurrent database writes passed!")


if __name__ == "__main__":
    asyncio.run(main())