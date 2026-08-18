import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.ws.connection_manager import connection_manager

router = APIRouter()


@router.websocket("/ws/agent-stream")
async def agent_stream(websocket: WebSocket, token: str) -> None:
    """Live feed of agent status updates for the authenticated user's org.

    Auth token is passed as a query param since browser WebSocket clients
    can't set custom headers on the handshake request.
    """
    try:
        user_id = uuid.UUID(decode_access_token(token))
    except ValueError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    connection_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(user_id, websocket)
