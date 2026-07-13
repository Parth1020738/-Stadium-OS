import pytest
import uuid
import jwt
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import settings

def test_websocket_auth_and_lifecycle():
    secret = settings.JWT_SECRET
    alg = "HS256"

    # 1. Test connection with invalid token
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/dashboard?token=bad_token") as ws:
            pass

    # 2. Test connection with valid token
    token = jwt.encode(
        {"sub": "operator", "user_id": 10, "roles": ["Operator"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    with client.websocket_connect(f"/ws/dashboard?token={token}") as ws:
        # Send heartbeat ping
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"
