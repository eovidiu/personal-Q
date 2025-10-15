"""
Integration tests for Settings API.
"""

import pytest
from httpx import AsyncClient
import sys
import os




@pytest.mark.asyncio
async def test_create_api_key_endpoint(test_app):
    """Test POST /settings/api-keys endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/settings/api-keys",
            json={
                "service_name": "test_service",
                "api_key": "test-key-12345",
                "is_active": True
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["service_name"] == "test_service"
    assert data["has_api_key"] is True


@pytest.mark.asyncio
async def test_list_api_keys_endpoint(test_app):
    """Test GET /settings/api-keys endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Create an API key first
        await client.post(
            "/api/v1/settings/api-keys",
            json={
                "service_name": "list_test",
                "api_key": "test-key",
                "is_active": True
            }
        )

        # List API keys
        response = await client.get("/api/v1/settings/api-keys")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_api_key_endpoint(test_app):
    """Test DELETE /settings/api-keys/{service_name} endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Create API key first
        await client.post(
            "/api/v1/settings/api-keys",
            json={
                "service_name": "delete_test",
                "api_key": "test-key",
                "is_active": True
            }
        )

        # Delete API key
        response = await client.delete("/api/v1/settings/api-keys/delete_test")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_test_connection_endpoint(test_app):
    """Test POST /settings/test-connection endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Create API key first
        await client.post(
            "/api/v1/settings/api-keys",
            json={
                "service_name": "connection_test",
                "api_key": "test-key",
                "is_active": True
            }
        )

        # Test connection
        response = await client.post(
            "/api/v1/settings/test-connection",
            json={"service_name": "connection_test"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["service_name"] == "connection_test"
