import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.ws.connection_manager import connection_manager

router = APIRouter()


@router.websocket("/ws/agent-stream")
async def agent_stream(websocket: WebSocket, token: str) -> None:
    """Live feed of agent status updates for the authenticated user's organization.

    Auth token is passed as a query param since browser WebSocket clients
    can't set custom headers on the handshake request. The token only
    carries a user id, so the organization is resolved with a lookup —
    every teammate connected to this org sees the same agent activity.
    """
    try:
        user_id = uuid.UUID(decode_access_token(token))
    except ValueError:
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        await websocket.close(code=4401)
        return

    organization_id = user.organization_id

    await websocket.accept()
    connection_manager.connect(organization_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(organization_id, websocket)
