"""
API routers for all endpoints.
"""

__all__ = [
    "agents",
    "tasks",
    "activities",
    "metrics",
    "settings",
    "websocket",
    "auth",
]

from app.routers import activities, agents, auth, metrics, settings, tasks, websocket
