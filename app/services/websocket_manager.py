from fastapi import WebSocket

class ConnectionManager:

    def __init__(self) -> None:
        # dictionary tracks live network connections
        self.active_connections: dict[str, WebSocket] = {}


    # Accepts the WebSocket handshake and registers the connected client in a dictionary.
    async def connect(
            self,
            websocket: WebSocket,
            client_id: str
    ) -> bool:

        # Avoid replacing an existing connection with the same ID
        if client_id in self.active_connections:
            await websocket.close(code=1080)
            return False

        await websocket.accept()

        self.active_connections[client_id] = websocket
        return True

    # Removes the WebSocket from active connections when the client disconnects.
    def disconnect(
            self,
            client_id: str,
            websocket: WebSocket
    ) -> None:

        if self.active_connections.get(client_id) is websocket:
            del self.active_connections[client_id]

            print(f"Client {client_id} disconnected")
            print(
                f"Active connections: {len(self.active_connections)}"
            )


    # Sends JSON data through an established connection using await
    async def send_message(
            self,
            client_id: str,
            message: dict
    ) -> None:

        websocket = self.active_connections.get(client_id)

        if websocket is not None:
            await websocket.send_json(message)



manager = ConnectionManager()

