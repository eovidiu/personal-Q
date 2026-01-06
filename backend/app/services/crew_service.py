"""
ABOUTME: CrewAI service for multi-agent orchestration and collaboration.
ABOUTME: Uses LangChain-compatible ChatAnthropic for proper integration.
"""

from typing import Any, Dict, List, Optional

from app.models.agent import Agent, AgentType
from app.services.llm_service import get_anthropic_api_key
from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession

# Try to import CrewAI, but provide stubs if not available
try:
    from crewai import Agent as CrewAgent
    from crewai import Crew, Process
    from crewai import Task as CrewTask
    from langchain_anthropic import ChatAnthropic

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Provide stub classes for type checking
    CrewAgent = None
    CrewTask = None
    Crew = None
    Process = None
    ChatAnthropic = None


class CrewService:
    """Service for CrewAI agent orchestration."""

    @staticmethod
    def _map_agent_type_to_role(agent_type: AgentType) -> str:
        """Map agent type to CrewAI role description."""
        role_mapping = {
            AgentType.CONVERSATIONAL: "Customer Support Specialist",
            AgentType.ANALYTICAL: "Data Analyst and Researcher",
            AgentType.CREATIVE: "Creative Content Writer",
            AgentType.AUTOMATION: "Automation and Workflow Specialist",
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
            llm=llm_instance,
        )

    @staticmethod
    async def execute_agent_task(
        db: AsyncSession, agent: Agent, task_description: str, task_input: Dict[str, Any] = None
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
        if not CREWAI_AVAILABLE:
            return {
                "success": False,
                "error": "CrewAI is not available. Please install crewai and crewai-tools packages.",
                "agent_id": agent.id,
                "task_description": task_description,
            }

        # Get API key from environment variable
        try:
            api_key = get_anthropic_api_key()
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent.id,
                "task_description": task_description,
            }

        # Configure LLM for agent using LangChain-compatible ChatAnthropic
        llm = ChatAnthropic(
            model=agent.model or settings.default_model,
            anthropic_api_key=api_key,
            temperature=agent.temperature or settings.default_temperature,
            max_tokens=agent.max_tokens or settings.default_max_tokens,
            streaming=True,  # Enable streaming for real-time responses
        )

        # Create CrewAI agent
        crew_agent = CrewService._create_crew_agent(agent, llm)

        # Create task
        crew_task = CrewTask(
            description=task_description,
            agent=crew_agent,
            expected_output="Detailed result of the task execution",
        )

        # Create crew with single agent
        crew = Crew(
            agents=[crew_agent], tasks=[crew_task], process=Process.sequential, verbose=True
        )

        # Execute
        try:
            result = crew.kickoff()

            return {
                "success": True,
                "result": str(result),
                "agent_id": agent.id,
                "task_description": task_description,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent.id,
                "task_description": task_description,
            }

    @staticmethod
    async def execute_multi_agent_task(
        db: AsyncSession,
        agents: List[Agent],
        task_descriptions: List[str],
        process: str = "sequential",
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
        if not CREWAI_AVAILABLE:
            return {
                "success": False,
                "error": "CrewAI is not available. Please install crewai and crewai-tools packages.",
                "agents": [{"id": a.id, "name": a.name} for a in agents],
            }

        if len(agents) != len(task_descriptions):
            raise ValueError("Number of agents must match number of tasks")

        # Get API key from environment variable
        try:
            api_key = get_anthropic_api_key()
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "agents": [{"id": a.id, "name": a.name} for a in agents],
            }

        # Use first agent's config as default for multi-agent crew
        primary_agent = agents[0]
        llm = ChatAnthropic(
            model=primary_agent.model or settings.default_model,
            anthropic_api_key=api_key,
            temperature=primary_agent.temperature or settings.default_temperature,
            max_tokens=primary_agent.max_tokens or settings.default_max_tokens,
            streaming=True,
        )

        # Create CrewAI agents
        crew_agents = [CrewService._create_crew_agent(agent, llm) for agent in agents]

        # Create tasks
        crew_tasks = [
            CrewTask(
                description=task_desc, agent=crew_agents[i], expected_output="Detailed task result"
            )
            for i, task_desc in enumerate(task_descriptions)
        ]

        # Determine process type
        process_type = Process.hierarchical if process == "hierarchical" else Process.sequential

        # Create crew
        crew = Crew(agents=crew_agents, tasks=crew_tasks, process=process_type, verbose=True)

        # Execute
        try:
            result = crew.kickoff()

            return {
                "success": True,
                "result": str(result),
                "agents": [{"id": a.id, "name": a.name} for a in agents],
                "process": process,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agents": [{"id": a.id, "name": a.name} for a in agents],
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
