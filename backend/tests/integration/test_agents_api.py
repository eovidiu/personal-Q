"""
Integration tests for Agent API endpoints.
"""

import pytest
from httpx import AsyncClient
import sys
import os


from app.main import app
from app.models.agent import AgentType, AgentStatus


@pytest.mark.asyncio
async def test_create_agent_endpoint():
    """Test POST /agents endpoint."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/agents",
            json={
                "name": "API Test Agent",
                "description": "Test agent via API",
                "agent_type": "conversational",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "You are a test agent.",
                "tags": ["test", "api"]
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Test Agent"
    assert data["agent_type"] == "conversational"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_agents_endpoint():
    """Test GET /agents endpoint."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/agents")

    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["agents"], list)


@pytest.mark.asyncio
async def test_get_agent_endpoint():
    """Test GET /agents/{id} endpoint."""
    # Create agent first
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        create_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Get Test Agent",
                "description": "Test",
                "agent_type": "analytical",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = create_response.json()["id"]

        # Get agent
        response = await client.get(f"/api/v1/agents/{agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "Get Test Agent"


@pytest.mark.asyncio
async def test_get_agent_not_found():
    """Test GET /agents/{id} with invalid ID."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/agents/invalid-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_agent_endpoint():
    """Test PUT /agents/{id} endpoint."""
    # Create agent first
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        create_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Update Test Agent",
                "description": "Original",
                "agent_type": "creative",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = create_response.json()["id"]

        # Update agent
        response = await client.put(
            f"/api/v1/agents/{agent_id}",
            json={"description": "Updated description"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_agent_status_endpoint():
    """Test PATCH /agents/{id}/status endpoint."""
    # Create agent first
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        create_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Status Test Agent",
                "description": "Test",
                "agent_type": "automation",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = create_response.json()["id"]

        # Update status
        response = await client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": "active"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_delete_agent_endpoint():
    """Test DELETE /agents/{id} endpoint."""
    # Create agent first
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        create_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Delete Test Agent",
                "description": "Test",
                "agent_type": "conversational",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = create_response.json()["id"]

        # Delete agent
        response = await client.delete(f"/api/v1/agents/{agent_id}")

    assert response.status_code == 204

    # Verify deletion
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_agents_with_filters():
    """Test GET /agents with query filters."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        # Create test agent
        await client.post(
            "/api/v1/agents",
            json={
                "name": "Filter Test Agent",
                "description": "Customer support agent",
                "agent_type": "conversational",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test.",
                "tags": ["support", "test"]
            }
        )

        # Filter by search
        response = await client.get("/api/v1/agents?search=customer")
        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) > 0

        # Filter by agent_type
        response = await client.get("/api/v1/agents?agent_type=conversational")
        assert response.status_code == 200
        assert all(a["agent_type"] == "conversational" for a in response.json()["agents"])
