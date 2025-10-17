"""
Integration tests for Metrics API.
"""

import pytest
from httpx import AsyncClient
import sys
import os




@pytest.mark.asyncio
async def test_get_dashboard_metrics(test_app):
    """Test GET /metrics/dashboard endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/metrics/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert "total_agents" in data
    assert "active_agents" in data
    assert "tasks_completed" in data
    assert "avg_success_rate" in data


@pytest.mark.asyncio
async def test_get_agent_metrics(test_app):
    """Test GET /metrics/agent/{id} endpoint."""
    # Create agent first
    async with AsyncClient(app=test_app, base_url="http://test", follow_redirects=True) as client:
        agent_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Metrics Test Agent",
                "description": "Test",
                "agent_type": "analytical",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = agent_response.json()["id"]

        # Get agent metrics
        response = await client.get(f"/api/v1/metrics/agent/{agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == agent_id
    assert "tasks_completed" in data
    assert "success_rate" in data


@pytest.mark.asyncio
async def test_get_memory_statistics(test_app):
    """Test GET /metrics/memory endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/metrics/memory")

    assert response.status_code == 200
    data = response.json()
    assert "memory_statistics" in data
    assert "storage_type" in data
