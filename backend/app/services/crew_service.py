"""
CrewAI service for agent orchestration.
"""

from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import sys

sys.path.insert(0, "/root/repo/backend")

from app.models.agent import Agent, AgentType
from app.services.llm_service import llm_service
from config.settings import settings


class CrewService:
    """Service for CrewAI agent orchestration."""

    @staticmethod
    def _map_agent_type_to_role(agent_type: AgentType) -> str:
        """Map agent type to CrewAI role description."""
        role_mapping = {
            AgentType.CONVERSATIONAL: "Customer Support Specialist",
            AgentType.ANALYTICAL: "Data Analyst and Researcher",
            AgentType.CREATIVE: "Creative Content Writer",
            AgentType.AUTOMATION: "Automation and Workflow Specialist"
        }
        return role_mapping.get(agent_type, "General Purpose Assistant")

    @staticmethod
    def _create_crew_agent(agent: Agent, llm_instance: Any) -> CrewAgent:
        """
        Create a CrewAI agent from database agent model.

        Args:
            agent: Database agent model
            llm_instance: LLM instance for the agent

        Returns:
            CrewAI Agent instance
        """
        role = CrewService._map_agent_type_to_role(agent.agent_type)

        return CrewAgent(
            role=role,
            goal=agent.description,
            backstory=agent.system_prompt,
            verbose=True,
            allow_delegation=True,
            llm=llm_instance
        )

    @staticmethod
    async def execute_agent_task(
        db: AsyncSession,
        agent: Agent,
        task_description: str,
        task_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with a single agent.

        Args:
            db: Database session
            agent: Agent to execute task
            task_description: Task description
            task_input: Task input data

        Returns:
            Task execution result
        """
        # Configure LLM for agent
        # Note: In production, get API key from database settings
        # For now using settings default
        from anthropic import Anthropic

        llm = Anthropic(api_key=llm_service.api_key or "dummy-key")

        # Create CrewAI agent
        crew_agent = CrewService._create_crew_agent(agent, llm)

        # Create task
        crew_task = CrewTask(
            description=task_description,
            agent=crew_agent,
            expected_output="Detailed result of the task execution"
        )

        # Create crew with single agent
        crew = Crew(
            agents=[crew_agent],
            tasks=[crew_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute
        try:
            result = crew.kickoff()

            return {
                "success": True,
                "result": str(result),
                "agent_id": agent.id,
                "task_description": task_description
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent.id,
                "task_description": task_description
            }

    @staticmethod
    async def execute_multi_agent_task(
        db: AsyncSession,
        agents: List[Agent],
        task_descriptions: List[str],
        process: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Execute tasks with multiple agents collaborating.

        Args:
            db: Database session
            agents: List of agents to collaborate
            task_descriptions: List of task descriptions (one per agent)
            process: "sequential" or "hierarchical"

        Returns:
            Execution result
        """
        if len(agents) != len(task_descriptions):
            raise ValueError("Number of agents must match number of tasks")

        from anthropic import Anthropic
        llm = Anthropic(api_key=llm_service.api_key or "dummy-key")

        # Create CrewAI agents
        crew_agents = [
            CrewService._create_crew_agent(agent, llm)
            for agent in agents
        ]

        # Create tasks
        crew_tasks = [
            CrewTask(
                description=task_desc,
                agent=crew_agents[i],
                expected_output="Detailed task result"
            )
            for i, task_desc in enumerate(task_descriptions)
        ]

        # Determine process type
        process_type = Process.hierarchical if process == "hierarchical" else Process.sequential

        # Create crew
        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=process_type,
            verbose=True
        )

        # Execute
        try:
            result = crew.kickoff()

            return {
                "success": True,
                "result": str(result),
                "agents": [{"id": a.id, "name": a.name} for a in agents],
                "process": process
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agents": [{"id": a.id, "name": a.name} for a in agents]
            }

    @staticmethod
    def create_agent_tools(agent: Agent) -> List[Any]:
        """
        Create tools for an agent based on its configuration.

        Args:
            agent: Agent model

        Returns:
            List of CrewAI tools
        """
        tools = []

        # Based on agent.tools_config, create appropriate tools
        # This will be implemented when we add external integrations

        return tools
