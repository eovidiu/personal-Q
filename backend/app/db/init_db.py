"""
Database initialization and seeding utilities.
"""

import asyncio
import sys
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.chroma_client import chroma_client
from app.db.database import AsyncSessionLocal, Base, engine
from app.models import Agent, AgentStatus, AgentType, APIKey
from app.utils.datetime_utils import utcnow


async def init_database():
    """Initialize database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


async def seed_default_data():
    """Seed database with default/sample data."""
    print("Seeding default data...")

    async with AsyncSessionLocal() as session:
        # Check if data already exists
        from sqlalchemy import select

        result = await session.execute(select(Agent))
        existing_agents = result.scalars().all()

        if existing_agents:
            print("Database already contains data. Skipping seeding.")
            return

        # Create sample agents matching the screenshot
        sample_agents = [
            {
                "id": str(uuid.uuid4()),
                "name": "Customer Support Bot",
                "description": "Handles customer inquiries and provides instant support across multiple channels",
                "agent_type": AgentType.CONVERSATIONAL,
                "status": AgentStatus.ACTIVE,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 4096,
                "system_prompt": "You are a helpful customer support assistant. Provide clear, concise, and friendly responses to customer inquiries.",
                "tags": ["support", "customer-service", "conversational"],
                "tasks_completed": 1247,
                "tasks_failed": 60,
                "last_active": utcnow(),
                "tools_config": {"slack": True, "email": True},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Data Analyst",
                "description": "Analyzes complex datasets and generates insights with visualizations",
                "agent_type": AgentType.ANALYTICAL,
                "status": AgentStatus.ACTIVE,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 8192,
                "system_prompt": "You are a data analyst. Analyze data, identify patterns, and provide actionable insights with clear visualizations.",
                "tags": ["analytics", "data", "analytical"],
                "tasks_completed": 856,
                "tasks_failed": 24,
                "last_active": utcnow(),
                "tools_config": {"onedrive": True, "obsidian": True},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Content Creator",
                "description": "Generates creative content including blog posts, social media, and marketing copy",
                "agent_type": AgentType.CREATIVE,
                "status": AgentStatus.ACTIVE,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.9,
                "max_tokens": 3072,
                "system_prompt": "You are a creative content writer. Generate engaging, original content that resonates with the target audience.",
                "tags": ["content", "marketing", "creative"],
                "tasks_completed": 543,
                "tasks_failed": 45,
                "last_active": utcnow(),
                "tools_config": {"obsidian": True},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Code Review Assistant",
                "description": "Reviews code for best practices, bugs, and security vulnerabilities",
                "agent_type": AgentType.ANALYTICAL,
                "status": AgentStatus.TRAINING,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.2,
                "max_tokens": 8192,
                "system_prompt": "You are a code review expert. Review code for best practices, potential bugs, security vulnerabilities, and suggest improvements.",
                "tags": ["analytical", "code", "review"],
                "tasks_completed": 234,
                "tasks_failed": 12,
                "last_active": utcnow(),
                "tools_config": {},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Email Automation",
                "description": "Automates email responses and manages inbox workflows",
                "agent_type": AgentType.AUTOMATION,
                "status": AgentStatus.INACTIVE,
                "model": "claude-3-opus-20240229",
                "temperature": 0.5,
                "max_tokens": 4096,
                "system_prompt": "You are an email automation assistant. Process emails, draft responses, and manage inbox workflows efficiently.",
                "tags": ["automation", "email"],
                "tasks_completed": 1892,
                "tasks_failed": 156,
                "last_active": None,
                "tools_config": {"outlook": True},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Research Assistant",
                "description": "Conducts research and summarizes findings from multiple sources",
                "agent_type": AgentType.ANALYTICAL,
                "status": AgentStatus.ERROR,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.4,
                "max_tokens": 8192,
                "system_prompt": "You are a research assistant. Conduct thorough research, synthesize information from multiple sources, and provide comprehensive summaries.",
                "tags": ["analytical", "research", "analysis"],
                "tasks_completed": 412,
                "tasks_failed": 32,
                "last_active": utcnow(),
                "tools_config": {"onedrive": True, "obsidian": True},
            },
        ]

        for agent_data in sample_agents:
            agent = Agent(**agent_data)
            session.add(agent)

        await session.commit()
        print(f"Seeded {len(sample_agents)} sample agents.")


async def init_chroma_collections():
    """Initialize ChromaDB collections."""
    print("Initializing ChromaDB collections...")

    # Create collections
    chroma_client.get_or_create_collection(
        name="conversations", metadata={"description": "Agent conversation history"}
    )

    chroma_client.get_or_create_collection(
        name="agent_outputs", metadata={"description": "Agent task outputs and results"}
    )

    chroma_client.get_or_create_collection(
        name="documents", metadata={"description": "Embedded documents for RAG"}
    )

    print("ChromaDB collections initialized.")


async def main():
    """Main initialization function."""
    print("=" * 50)
    print("Personal-Q Database Initialization")
    print("=" * 50)

    # Initialize database
    await init_database()

    # Seed default data
    await seed_default_data()

    # Initialize ChromaDB
    await init_chroma_collections()

    print("=" * 50)
    print("Initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
