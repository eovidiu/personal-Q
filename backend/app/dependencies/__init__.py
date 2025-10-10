"""
Dependency injection modules for FastAPI.
Includes authentication, database, and other shared dependencies.
"""

__all__ = [
    "get_current_user",
    "get_optional_user",
]

from .auth import get_current_user, get_optional_user
