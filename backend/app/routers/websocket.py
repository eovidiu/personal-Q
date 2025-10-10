"""
WebSocket endpoints for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        # Remove from all subscriptions
        for event_type in list(self.subscriptions.keys()):
            self.subscriptions[event_type].discard(websocket)

    async def subscribe(self, websocket: WebSocket, event_type: str):
        """Subscribe connection to event type."""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = set()
        self.subscriptions[event_type].add(websocket)

    async def broadcast(self, event_type: str, message: dict):
        """Broadcast message to subscribed connections."""
        if event_type not in self.subscriptions:
            return

        disconnected = set()
        for connection in self.subscriptions[event_type]:
            try:
                await connection.send_json({
                    "event_type": event_type,
                    "data": message,
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat()
                })
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection endpoint."""
    await manager.connect(websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    # Subscribe to event types
                    event_types = message.get("event_types", [])
                    for event_type in event_types:
                        await manager.subscribe(websocket, event_type)

                    await websocket.send_json({
                        "status": "subscribed",
                        "event_types": event_types
                    })

                elif action == "ping":
                    # Heartbeat
                    await websocket.send_json({"status": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_event(event_type: str, data: dict):
    """
    Broadcast event to subscribers.

    Event types:
    - agent_status_changed
    - task_started
    - task_completed
    - task_failed
    - activity_created
    """
    await manager.broadcast(event_type, data)


def get_connection_manager() -> ConnectionManager:
    """Get WebSocket connection manager."""
    return manager
