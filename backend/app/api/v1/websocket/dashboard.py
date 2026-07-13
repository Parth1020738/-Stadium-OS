import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from typing import Dict, Set, Optional
import jwt
from backend.app.core.security import settings
from backend.app.core.redis import redis_manager

logger = logging.getLogger("dashboard_websocket")
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps channel names to sets of WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "overview": set(),
            "crowd": set(),
            "incidents": set(),
            "transit": set(),
            "volunteers": set(),
            "accessibility": set(),
            "alerts": set(),
            "metrics": set()
        }

    async def connect(self, websocket: WebSocket, channel: str, token: str) -> bool:
        # Validate JWT token
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            # Verification succeeded
            await websocket.accept()
            if channel in self.active_connections:
                self.active_connections[channel].add(websocket)
            else:
                self.active_connections[channel] = {websocket}
            logger.info(f"WebSocket client connected to channel '{channel}'")
            return True
        except jwt.PyJWTError as e:
            logger.warning(f"WebSocket JWT authentication failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return False

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
        logger.info(f"WebSocket client disconnected from channel '{channel}'")

    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            disconnected_sockets = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending message to WebSocket: {e}")
                    disconnected_sockets.add(connection)
            for dead_socket in disconnected_sockets:
                self.active_connections[channel].discard(dead_socket)


manager = ConnectionManager()


async def redis_pubsub_listener():
    """Background listener task for Redis pub/sub to forward to WebSockets."""
    pubsub = redis_manager.client.pubsub()
    await pubsub.subscribe("dashboard:updates")
    logger.info("Subscribed to Redis channel 'dashboard:updates'")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    channel = data.get("channel", "overview")
                    payload = data.get("payload", {})
                    await manager.broadcast(channel, payload)
                except Exception as e:
                    logger.error(f"Error parsing Redis pubsub message: {e}")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe("dashboard:updates")


# Start pubsub listener in background task during lifespan/startup if needed,
# or simulate via endpoint heartbeat.

async def handle_ws_lifecycle(websocket: WebSocket, channel: str, token: str):
    success = await manager.connect(websocket, channel, token)
    if not success:
        return

    try:
        while True:
            # Heartbeat check/receiver
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/dashboard")
async def ws_dashboard_overview(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "overview", token)

@router.websocket("/ws/dashboard/crowd")
async def ws_dashboard_crowd(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "crowd", token)

@router.websocket("/ws/dashboard/incidents")
async def ws_dashboard_incidents(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "incidents", token)

@router.websocket("/ws/dashboard/transit")
async def ws_dashboard_transit(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "transit", token)

@router.websocket("/ws/dashboard/volunteers")
async def ws_dashboard_volunteers(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "volunteers", token)

@router.websocket("/ws/dashboard/accessibility")
async def ws_dashboard_accessibility(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "accessibility", token)

@router.websocket("/ws/dashboard/alerts")
async def ws_dashboard_alerts(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "alerts", token)

@router.websocket("/ws/dashboard/metrics")
async def ws_dashboard_metrics(websocket: WebSocket, token: str = Query(...)):
    await handle_ws_lifecycle(websocket, "metrics", token)
