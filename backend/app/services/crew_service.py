"""
ABOUTME: CrewAI service for multi-agent orchestration and collaboration.
ABOUTME: Uses CrewAI native LLM with Anthropic provider.
"""

from typing import Any, Dict, List, Optional

from app.models.agent import Agent, AgentType
from app.services.llm_service import get_anthropic_api_key
from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession

# Try to import CrewAI, but provide stubs if not available
try:
    from crewai import Agent as CrewAgent
    from crewai import Crew, LLM, Process
    from crewai import Task as CrewTask

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Provide stub classes for type checking
    CrewAgent = None
    CrewTask = None
    Crew = None
    Process = None
    LLM = None


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

        # Configure LLM using CrewAI native LLM with anthropic/ prefix
        model_name = agent.model or settings.default_model
        # Ensure model has anthropic/ prefix for proper routing
        if not model_name.startswith("anthropic/"):
            model_name = f"anthropic/{model_name}"

        llm = LLM(
            model=model_name,
            api_key=api_key,
            temperature=agent.temperature or settings.default_temperature,
            max_tokens=agent.max_tokens or settings.default_max_tokens,
        )

        # Create CrewAI agent
        crew_agent = CrewService._create_crew_agent(agent, llm)

        # Create task
        crew_task = CrewTask(
            description=task_description,
            agent=crew_agent,
            expected_output="Detailed result of the task execution",
        )

        # Create crew with single agent (memory disabled to avoid OpenAI embeddings)
        crew = Crew(
            agents=[crew_agent],
            tasks=[crew_task],
            process=Process.sequential,
            verbose=True,
            memory=False,  # Disable memory to avoid OpenAI embeddings requirement
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
        model_name = primary_agent.model or settings.default_model
        # Ensure model has anthropic/ prefix for proper routing
        if not model_name.startswith("anthropic/"):
            model_name = f"anthropic/{model_name}"

        llm = LLM(
            model=model_name,
            api_key=api_key,
            temperature=primary_agent.temperature or settings.default_temperature,
            max_tokens=primary_agent.max_tokens or settings.default_max_tokens,
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

        # Create crew (memory disabled to avoid OpenAI embeddings requirement)
        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=process_type,
            verbose=True,
            memory=False,
        )

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
