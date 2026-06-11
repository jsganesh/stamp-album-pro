"""
Tests for WebSocket real-time preview (P2-13).
"""
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from stamp_album.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestWebSocketPreview:
    """Tests for the WebSocket preview endpoint."""

    def test_websocket_connection(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert "client_id" in data

    def test_websocket_render(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            ws.receive_json() # connected message
            ws.send_json({"type": "render", "dsl": 'ALBUM_TITLE("Test")\nPAGE_START\nPAGE_TEXT("HN" 12 "Hello")'})
            data = ws.receive_json()
            assert data["type"] == "preview"
            assert data["status"] == "ok"
            assert "html" in data

    def test_websocket_empty_dsl(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            ws.receive_json() # connected
            ws.send_json({"type": "render", "dsl": ""})
            data = ws.receive_json()
            assert data["type"] == "preview"
            assert data["status"] == "empty"

    def test_websocket_invalid_dsl(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            ws.receive_json() # connected
            ws.send_json({"type": "render", "dsl": "PAGE_TEXT outside page"})
            data = ws.receive_json()
            assert data["type"] == "error"

    def test_websocket_ping_pong(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            ws.receive_json() # connected
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_websocket_validate(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            ws.receive_json() # connected
            ws.send_json({"type": "validate", "dsl": 'ALBUM_TITLE("Test")\nPAGE_START'})
            data = ws.receive_json()
            assert data["type"] == "validation"
            assert data["valid"] is True

    def test_websocket_invalid_json(self, client):
        with client.websocket_connect("/ws/preview") as ws:
            ws.receive_json() # connected
            ws.send_text("not json")
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "Invalid JSON" in data["message"]
