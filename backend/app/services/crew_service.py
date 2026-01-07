"""
ABOUTME: CrewAI service for multi-agent orchestration and collaboration.
ABOUTME: Supports multiple LLM providers via ModelValidator and ProviderRegistry.
ABOUTME: API keys are ONLY read from environment variables - NEVER from database.
"""

import logging
from typing import Any, Dict, List

from app.models.agent import Agent, AgentType
from app.services.model_validator import ModelValidator, model_validator
from app.services.provider_registry import provider_registry
from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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
    """Service for CrewAI agent orchestration with multi-provider support."""

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
    def _resolve_llm(
        model_string: str, validator: ModelValidator = None
    ) -> tuple[Any, str, Dict[str, Any]]:
        """
        Resolve and create an LLM instance from a model string.

        SECURITY: API keys are ONLY read from environment variables.
        They are NEVER stored in the database.

        Args:
            model_string: Model string (e.g., "anthropic/claude-3-5-sonnet-20241022" or "GPT-4")
            validator: ModelValidator instance (optional)

        Returns:
            Tuple of (LLM instance, normalized model string, error dict or None)
        """
        validator = validator or model_validator

        # Validate and normalize the model string
        validation = validator.validate_model(model_string, check_configured=True)

        if not validation.is_valid:
            return None, None, {"error": validation.error}

        # Get API key from environment (NEVER from database)
        api_key = provider_registry.get_api_key(validation.provider)

        if not api_key:
            provider_config = provider_registry.get_provider(validation.provider)
            env_var = provider_config.api_key_env if provider_config else "API_KEY"
            return None, None, {
                "error": f"API key not configured for provider '{validation.provider}'. "
                f"Set {env_var} environment variable."
            }

        logger.info(
            f"Creating LLM for provider '{validation.provider}' "
            f"with model '{validation.model}'"
        )

        return validation.normalized, api_key, None

    @staticmethod
    async def execute_agent_task(
        db: AsyncSession,
        agent: Agent,
        task_description: str,
        task_input: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task with a single agent.

        Supports multiple LLM providers (Anthropic, OpenAI, Mistral).

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

        # Resolve model and get API key (from environment only)
        model_string = agent.model or settings.default_model
        normalized_model, api_key, error = CrewService._resolve_llm(model_string)

        if error:
            return {
                "success": False,
                "error": error["error"],
                "agent_id": agent.id,
                "task_description": task_description,
            }

        # Create LLM instance
        llm = LLM(
            model=normalized_model,
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
            logger.info(
                f"Executing task for agent '{agent.name}' with model '{normalized_model}'"
            )
            result = crew.kickoff()

            return {
                "success": True,
                "result": str(result),
                "agent_id": agent.id,
                "task_description": task_description,
                "model_used": normalized_model,
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
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

        Supports multiple LLM providers (Anthropic, OpenAI, Mistral).

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

        # Use first agent's model as default for multi-agent crew
        primary_agent = agents[0]
        model_string = primary_agent.model or settings.default_model
        normalized_model, api_key, error = CrewService._resolve_llm(model_string)

        if error:
            return {
                "success": False,
                "error": error["error"],
                "agents": [{"id": a.id, "name": a.name} for a in agents],
            }

        # Create shared LLM instance
        llm = LLM(
            model=normalized_model,
            api_key=api_key,
            temperature=primary_agent.temperature or settings.default_temperature,
            max_tokens=primary_agent.max_tokens or settings.default_max_tokens,
        )

        # Create CrewAI agents
        crew_agents = [CrewService._create_crew_agent(agent, llm) for agent in agents]

        # Create tasks
        crew_tasks = [
            CrewTask(
                description=task_desc,
                agent=crew_agents[i],
                expected_output="Detailed task result",
            )
            for i, task_desc in enumerate(task_descriptions)
        ]

        # Determine process type
        process_type = (
            Process.hierarchical if process == "hierarchical" else Process.sequential
        )

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
            logger.info(
                f"Executing multi-agent task with {len(agents)} agents, "
                f"model '{normalized_model}', process '{process}'"
            )
            result = crew.kickoff()

            return {
                "success": True,
                "result": str(result),
                "agents": [{"id": a.id, "name": a.name} for a in agents],
                "process": process,
                "model_used": normalized_model,
            }

        except Exception as e:
            logger.error(f"Multi-agent task execution failed: {e}", exc_info=True)
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
