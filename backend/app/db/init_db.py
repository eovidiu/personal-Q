"""
Database initialization and seeding utilities.
"""

import asyncio
import sys
import uuid
from datetime import datetime

from app.db.lance_client import (
    AgentOutputSchema,
    ConversationSchema,
    DocumentSchema,
    lance_client,
)
from app.db.database import AsyncSessionLocal, Base, engine
from app.models import Agent, AgentStatus, AgentType, APIKey
from app.utils.datetime_utils import utcnow
from sqlalchemy.ext.asyncio import AsyncSession


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

        # Create sample agents
        sample_agents = [
            {
                "id": str(uuid.uuid4()),
                "name": "Slack Agent",
                "description": "Retrieves last day's messages from Slack channels and direct messages",
                "agent_type": AgentType.AUTOMATION,
                "status": AgentStatus.ACTIVE,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.5,
                "max_tokens": 4096,
                "system_prompt": "You are a Slack integration agent. Retrieve and summarize messages from the last 24 hours, highlighting important conversations, mentions, and action items.",
                "tags": ["slack", "messaging", "automation", "communication"],
                "tasks_completed": 567,
                "tasks_failed": 12,
                "last_active": utcnow(),
                "tools_config": {"slack": True},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Outlook Agent",
                "description": "Retrieves last week's emails from Outlook inbox and organizes by priority",
                "agent_type": AgentType.AUTOMATION,
                "status": AgentStatus.ACTIVE,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.4,
                "max_tokens": 8192,
                "system_prompt": "You are an Outlook email agent. Retrieve emails from the past week, categorize them by importance, identify action items, and provide a comprehensive summary.",
                "tags": ["outlook", "email", "automation", "productivity"],
                "tasks_completed": 892,
                "tasks_failed": 23,
                "last_active": utcnow(),
                "tools_config": {"outlook": True},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Teams Agent",
                "description": "Retrieves last week's meeting notes from Microsoft Teams and extracts key decisions",
                "agent_type": AgentType.ANALYTICAL,
                "status": AgentStatus.ACTIVE,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 8192,
                "system_prompt": "You are a Microsoft Teams meeting assistant. Retrieve meeting notes and recordings from the past week, extract key decisions, action items, and follow-ups. Organize findings by project or team.",
                "tags": ["teams", "meetings", "analytical", "collaboration"],
                "tasks_completed": 445,
                "tasks_failed": 8,
                "last_active": utcnow(),
                "tools_config": {"teams": True, "onedrive": True},
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
                "name": "Research Assistant",
                "description": "Conducts research and summarizes findings from multiple sources",
                "agent_type": AgentType.ANALYTICAL,
                "status": AgentStatus.PAUSED,
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


async def init_lance_tables():
    """Initialize LanceDB tables."""
    print("Initializing LanceDB tables...")

    # Create tables with schemas
    lance_client.get_or_create_table(name="conversations", schema=ConversationSchema)
    lance_client.get_or_create_table(name="agent_outputs", schema=AgentOutputSchema)
    lance_client.get_or_create_table(name="documents", schema=DocumentSchema)

    print("LanceDB tables initialized.")


async def main():
    """Main initialization function."""
    print("=" * 50)
    print("Personal-Q Database Initialization")
    print("=" * 50)

    # Initialize database
    await init_database()

    # Seed default data
    await seed_default_data()

    # Initialize LanceDB
    await init_lance_tables()

    print("=" * 50)
    print("Initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
