import uuid

from app.core.security import create_access_token


def test_agent_stream_rejects_invalid_token(client):
    try:
        with client.websocket_connect("/ws/agent-stream?token=not-a-real-token"):
            pass
    except Exception:
        pass
    else:
        assert False, "expected the connection to be rejected"


def test_agent_stream_accepts_valid_token(client):
    token = create_access_token(subject=str(uuid.uuid4()))

    with client.websocket_connect(f"/ws/agent-stream?token={token}") as websocket:
        websocket.close()
