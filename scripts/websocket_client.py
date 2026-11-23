import asyncio
import json

from websockets.asyncio.client import connect

async def main():
    url = "ws://127.0.0.1:8000/ws/client-1"

    async with connect(url) as websocket:
        # First message: start a conversation
        await websocket.send(json.dumps({
            "message": "Hello"
        }))

        first = json.loads(await websocket.recv())

        print("First response:", first)

        conversation_id = first["conversation_id"]

        # Second message: continue the conversation
        await websocket.send(json.dumps({
            "message": "What is Python?",
            "conversation_id": conversation_id
        }))

        second = json.loads(await websocket.recv())

        print("\nSecond response:", second)

        # third message: thanks
        await websocket.send(json.dumps({
            "message": "Thank you",
            "conversation_id": conversation_id
        }))

        third = json.loads(await websocket.recv())

        print("\nThird response:", third)

        await websocket.send(json.dumps({
            "message": "hello",
            "conversation_id": "invalid-123"
        }))

        response = json.loads(await websocket.recv())

        if response.get("type") == "error":
            print("\nError received:")
            print("Status code:", response.get("status_code"))
            print("Message:", response.get("detail"))

        else:
            print("\nChatbot response:")
            print(response["message"]["content"])


        print(
            "\nTotal messages:",
            len(third["conversation_history"])
        )


if __name__ == "__main__":
    asyncio.run(main())
