"""
Integration tests for Activities API.
"""

import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.main import app


@pytest.mark.asyncio
async def test_list_activities_endpoint():
    """Test GET /activities endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/activities")

    assert response.status_code == 200
    data = response.json()
    assert "activities" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["activities"], list)


@pytest.mark.asyncio
async def test_list_activities_with_filters():
    """Test GET /activities with query parameters."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create an agent to generate activities
        agent_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Activity Test Agent",
                "description": "Test",
                "agent_type": "conversational",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = agent_response.json()["id"]

        # List activities for this agent
        response = await client.get(f"/api/v1/activities?agent_id={agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert "activities" in data


@pytest.mark.asyncio
async def test_list_activities_pagination():
    """Test activities pagination."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get first page
        response = await client.get("/api/v1/activities?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
