"""
WebSocket endpoints for real-time updates with JWT authentication.

SECURITY: Authentication is done via first-message protocol, not URL parameters.
This prevents JWT tokens from being logged in server logs, browser history,
and proxy caches.
"""

import json
import logging
from typing import Dict, Optional, Set

import jwt
from app.utils.datetime_utils import utcnow
from config.settings import settings
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)
router = APIRouter()

# Security constants
MAX_MESSAGE_SIZE = 64 * 1024  # 64KB limit for WebSocket messages
AUTH_TIMEOUT_SECONDS = 10  # Time allowed for authentication after connection


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
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket connection endpoint with first-message authentication.

    SECURITY: Authentication is done via first message, NOT URL query parameters.
    This prevents JWT tokens from being exposed in server logs, browser history,
    and proxy caches.

    Connection flow:
    1. Client connects to ws://host/ws/ (no token in URL)
    2. Server accepts connection and waits for auth message
    3. Client sends: {"action": "authenticate", "token": "jwt_token"}
    4. Server validates token and either confirms or closes connection

    After authentication, supported actions:
    - subscribe: Subscribe to event types
    - ping: Heartbeat check
    """
    # Accept connection first (authentication via first message)
    await websocket.accept()
    logger.info("WebSocket connection accepted, awaiting authentication...")

    user = None

    try:
        # Wait for authentication message (with timeout handled by client/server config)
        auth_data = await websocket.receive_text()

        # Validate message size
        if len(auth_data) > MAX_MESSAGE_SIZE:
            logger.warning("WebSocket: Authentication message too large")
            await websocket.send_json({"error": "Message too large", "max_size": MAX_MESSAGE_SIZE})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Message too large")
            return

        try:
            auth_message = json.loads(auth_data)
        except json.JSONDecodeError:
            logger.warning("WebSocket: Invalid JSON in authentication message")
            await websocket.send_json({"error": "Invalid JSON"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication format")
            return

        # Verify this is an authentication message
        if auth_message.get("action") != "authenticate":
            logger.warning(f"WebSocket: First message must be authentication, got: {auth_message.get('action')}")
            await websocket.send_json({"error": "First message must be authentication", "expected_action": "authenticate"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
            return

        # Validate token
        token = auth_message.get("token")
        user = await verify_websocket_token(token)

        if not user:
            logger.warning("WebSocket: Authentication failed - invalid token")
            await websocket.send_json({"error": "Authentication failed", "reason": "Invalid or expired token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            return

        # Authentication successful
        logger.info(f"WebSocket authenticated for user: {user.get('email')}")
        await websocket.send_json({"status": "authenticated", "email": user.get("email")})

        # Add to connection manager after successful auth
        manager.active_connections.add(websocket)

        # Main message loop
        while True:
            data = await websocket.receive_text()

            # Validate message size (MEDIUM-003 fix)
            if len(data) > MAX_MESSAGE_SIZE:
                logger.warning(f"WebSocket: Message too large ({len(data)} bytes)")
                await websocket.send_json({"error": "Message too large", "max_size": MAX_MESSAGE_SIZE})
                continue

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

                elif action == "authenticate":
                    # Already authenticated, ignore re-auth attempts
                    await websocket.send_json({"status": "already_authenticated"})

                else:
                    await websocket.send_json({"error": f"Unknown action: {action}"})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user.get('email') if user else 'unauthenticated'}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
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
