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

from app.routers import agents, tasks, activities, metrics, settings, websocket, auth
