"""
WebSocket endpoints for real-time updates with JWT authentication.
"""

import json
import logging
from typing import Dict, Optional, Set

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.utils.datetime_utils import utcnow
from config.settings import settings

logger = logging.getLogger(__name__)
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
                await connection.send_json(
                    {"event_type": event_type, "data": message, "timestamp": utcnow().isoformat()}
                )
            except Exception as e:
                # Connection failed, mark for cleanup
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(connection)

        # Clean up disconnected
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


async def verify_websocket_token(token: Optional[str]) -> Optional[dict]:
    """
    Verify JWT token for WebSocket connection.

    Args:
        token: JWT token from query parameter

    Returns:
        Decoded payload if valid, None otherwise
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

        # Verify email matches allowed user
        if payload.get("email") != settings.allowed_email:
            logger.warning(f"WebSocket: Unauthorized email in token: {payload.get('email')}")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket: Expired token")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"WebSocket: Invalid token - {e}")
        return None
    except Exception as e:
        logger.error(f"WebSocket: Token verification error - {e}")
        return None


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket connection endpoint with authentication.

    Connection requires a valid JWT token passed as a query parameter:
    ws://localhost:8000/ws/?token=<your_jwt_token>
    """
    # Verify authentication before accepting connection
    user = await verify_websocket_token(token)
    if not user:
        logger.warning("WebSocket connection rejected: Invalid or missing token")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required"
        )
        return

    logger.info(f"WebSocket connection authenticated for user: {user.get('email')}")
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

                    await websocket.send_json({"status": "subscribed", "event_types": event_types})

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
