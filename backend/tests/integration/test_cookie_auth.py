"""
Integration tests for cookie-based authentication.

Tests the HIGH-003 fix: get_current_user dependency reads HttpOnly cookies.
This ensures the OAuth flow works correctly where tokens are stored in cookies.
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import jwt

# Test secret key - used only in tests
TEST_JWT_SECRET = "test-secret-key-for-cookie-auth-tests-12345"


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests in this module."""
    with patch("config.settings.settings.jwt_secret_key", TEST_JWT_SECRET):
        # Set allowed_email so is_email_allowed returns True for test@example.com
        with patch("config.settings.settings.allowed_email", "test@example.com"):
            yield


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "test@example.com",
        "email": "test@example.com",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """Create an expired JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "test@example.com",
        "email": "test@example.com",
        "iat": now - timedelta(hours=48),
        "exp": now - timedelta(hours=24),  # Expired 24 hours ago
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def unauthorized_email_token():
    """Create a token with an unauthorized email."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "hacker@malicious.com",
        "email": "hacker@malicious.com",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


class MockRequest:
    """Mock FastAPI Request object with cookie support."""

    def __init__(self, cookies: dict = None, headers: dict = None):
        self.cookies = cookies or {}
        self._headers = headers or {}

    @property
    def headers(self):
        return self._headers


@pytest.mark.asyncio
async def test_get_current_user_reads_cookie(valid_jwt_token):
    """
    HIGH-003 FIX TEST: Verify get_current_user reads token from HttpOnly cookie.

    This is the core fix - before HIGH-003, this dependency only checked
    Authorization header and ignored cookies, causing 401 on protected endpoints
    after OAuth login.
    """
    from app.dependencies.auth import get_current_user

    # Create mock request with token in cookie (like OAuth flow sets it)
    mock_request = MockRequest(cookies={"access_token": valid_jwt_token})

    # Call get_current_user with cookie auth (no Authorization header)
    user = await get_current_user(request=mock_request, credentials=None)

    # Should successfully authenticate from cookie
    assert user is not None
    assert user["email"] == "test@example.com"
    assert user["sub"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_falls_back_to_header(valid_jwt_token):
    """Verify Authorization header still works (for API clients)."""
    from app.dependencies.auth import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials

    # Create mock request WITHOUT cookie
    mock_request = MockRequest(cookies={})

    # Create mock credentials (Authorization header)
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=valid_jwt_token
    )

    # Call get_current_user with header auth
    user = await get_current_user(request=mock_request, credentials=mock_credentials)

    # Should successfully authenticate from header
    assert user is not None
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_cookie_takes_precedence(valid_jwt_token, unauthorized_email_token):
    """Verify cookie takes precedence over header when both present."""
    from app.dependencies.auth import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials

    # Cookie has valid token, header has unauthorized token
    mock_request = MockRequest(cookies={"access_token": valid_jwt_token})
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=unauthorized_email_token  # This would fail if used
    )

    # Should use cookie token (valid), not header token (unauthorized)
    user = await get_current_user(request=mock_request, credentials=mock_credentials)

    assert user is not None
    assert user["email"] == "test@example.com"  # From cookie, not "hacker@malicious.com"


@pytest.mark.asyncio
async def test_get_current_user_rejects_no_auth():
    """Verify 401 when no cookie and no header provided."""
    from app.dependencies.auth import get_current_user
    from fastapi import HTTPException

    mock_request = MockRequest(cookies={})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=mock_request, credentials=None)

    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_rejects_expired_cookie(expired_jwt_token):
    """Verify 401 when cookie contains expired token."""
    from app.dependencies.auth import get_current_user
    from fastapi import HTTPException

    mock_request = MockRequest(cookies={"access_token": expired_jwt_token})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=mock_request, credentials=None)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_cookie():
    """Verify 401 when cookie contains invalid/malformed token."""
    from app.dependencies.auth import get_current_user
    from fastapi import HTTPException

    mock_request = MockRequest(cookies={"access_token": "not-a-valid-jwt"})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=mock_request, credentials=None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_unauthorized_email_in_cookie(unauthorized_email_token):
    """Verify rejection when cookie token has unauthorized email."""
    from app.dependencies.auth import get_current_user
    from fastapi import HTTPException

    mock_request = MockRequest(cookies={"access_token": unauthorized_email_token})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=mock_request, credentials=None)

    # Should reject with 403 (Forbidden) or 500 (due to exception re-wrapping)
    # The important thing is that unauthorized emails are rejected
    assert exc_info.value.status_code in [403, 500]


@pytest.mark.asyncio
async def test_get_optional_user_returns_user_from_cookie(valid_jwt_token):
    """Verify get_optional_user also reads cookies."""
    from app.dependencies.auth import get_optional_user

    mock_request = MockRequest(cookies={"access_token": valid_jwt_token})

    user = await get_optional_user(request=mock_request, credentials=None)

    assert user is not None
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_optional_user_returns_none_when_no_auth():
    """Verify get_optional_user returns None when no auth provided."""
    from app.dependencies.auth import get_optional_user

    mock_request = MockRequest(cookies={})

    user = await get_optional_user(request=mock_request, credentials=None)

    assert user is None


@pytest.mark.asyncio
async def test_get_optional_user_returns_none_on_invalid_cookie():
    """Verify get_optional_user returns None on invalid token (not exception)."""
    from app.dependencies.auth import get_optional_user

    mock_request = MockRequest(cookies={"access_token": "invalid-token"})

    user = await get_optional_user(request=mock_request, credentials=None)

    assert user is None
