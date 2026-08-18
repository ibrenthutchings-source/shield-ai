import logging
import uuid
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class _SendableWebSocket(Protocol):
    async def send_json(self, data: Any) -> None: ...


class ConnectionManager:
    """Tracks live /ws/agent-stream sockets per user and fans out agent status updates."""

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[_SendableWebSocket]] = {}

    def connect(self, user_id: uuid.UUID, websocket: _SendableWebSocket) -> None:
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: _SendableWebSocket) -> None:
        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast(self, user_id: uuid.UUID, message: dict) -> None:
        for websocket in list(self._connections.get(user_id, ())):
            try:
                await websocket.send_json(message)
            except Exception:
                logger.warning("Dropping dead agent-stream socket for user %s", user_id)
                self.disconnect(user_id, websocket)


connection_manager = ConnectionManager()
