import uuid

from app.ws.connection_manager import ConnectionManager


class _FakeSocket:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[dict] = []

    async def send_json(self, data: dict) -> None:
        if self.fail:
            raise ConnectionError("socket closed")
        self.sent.append(data)


async def test_broadcast_delivers_to_all_sockets_for_user():
    manager = ConnectionManager()
    user_id = uuid.uuid4()
    socket_a, socket_b = _FakeSocket(), _FakeSocket()
    manager.connect(user_id, socket_a)
    manager.connect(user_id, socket_b)

    await manager.broadcast(user_id, {"status": "started"})

    assert socket_a.sent == [{"status": "started"}]
    assert socket_b.sent == [{"status": "started"}]


async def test_broadcast_only_reaches_the_targeted_user():
    manager = ConnectionManager()
    user_a, user_b = uuid.uuid4(), uuid.uuid4()
    socket_a, socket_b = _FakeSocket(), _FakeSocket()
    manager.connect(user_a, socket_a)
    manager.connect(user_b, socket_b)

    await manager.broadcast(user_a, {"status": "started"})

    assert socket_a.sent == [{"status": "started"}]
    assert socket_b.sent == []


async def test_dead_socket_is_dropped_on_send_failure():
    manager = ConnectionManager()
    user_id = uuid.uuid4()
    dead_socket = _FakeSocket(fail=True)
    manager.connect(user_id, dead_socket)

    await manager.broadcast(user_id, {"status": "started"})

    assert manager._connections.get(user_id) is None


def test_disconnect_removes_socket_and_empty_user_entry():
    manager = ConnectionManager()
    user_id = uuid.uuid4()
    socket = _FakeSocket()
    manager.connect(user_id, socket)

    manager.disconnect(user_id, socket)

    assert manager._connections.get(user_id) is None


def test_disconnect_of_unknown_socket_is_a_no_op():
    manager = ConnectionManager()
    manager.disconnect(uuid.uuid4(), _FakeSocket())
