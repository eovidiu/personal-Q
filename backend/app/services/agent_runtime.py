"""
ABOUTME: Claude agent runtime — a self-hosted tool-use agentic loop on the Anthropic SDK.
ABOUTME: Replaces the CrewAI/LiteLLM orchestration layer with the Messages API + tool use.

This module is the execution engine for agents. Instead of delegating to CrewAI
(which wrapped LiteLLM and LangChain), it drives Claude directly through the
official Anthropic SDK using an agentic loop:

    while not done:
        response = client.messages.create(model, system, messages, tools)
        if response wants a tool -> run the tool, append the result, continue
        else -> done

Tools are optional. With an empty tool set the loop degenerates to a single
Messages API call, which is the common case today. The loop is structured so
that real tools (web search, integrations, etc.) can be added later by
registering a handler in ``TOOL_HANDLERS`` and exposing a schema from
``build_tools``.

SECURITY: API keys are ONLY read from environment variables (via the provider
registry) — NEVER from the database.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from anthropic import (
    APIConnectionError,
    APIError,
    AsyncAnthropic,
    RateLimitError,
)
from app.models.agent import Agent, AgentType
from app.security.prompt_sanitizer import PromptSanitizer
from app.services.model_validator import ModelValidator, model_validator
from app.services.provider_registry import provider_registry
from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Maximum number of model<->tool round trips before we stop the loop. With no
# tools registered this is effectively a single call; the cap protects against
# runaway tool loops once tools are added.
MAX_AGENT_ITERATIONS = 10

# Timeout configuration (seconds) — mirrors LLMService.
TIMEOUT_CONNECT = 5.0
TIMEOUT_READ = 60.0
TIMEOUT_WRITE = 10.0
TIMEOUT_POOL = 5.0

# Model families that REJECT sampling params (temperature/top_p/top_k) and the
# legacy `thinking.budget_tokens` config. Sending those to these models returns
# a 400. We therefore omit temperature for any model whose id starts with one of
# these prefixes. See the Anthropic model migration guide.
_NO_SAMPLING_PARAM_PREFIXES = (
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-fable-5",
    "claude-mythos-5",
)


# A tool handler takes the tool input dict and returns a string result.
ToolHandler = Callable[[Dict[str, Any]], Awaitable[str]]

# Registry of built-in tool handlers, keyed by tool name. Empty by default.
# Register entries here (and expose a matching schema from ``build_tools``) to
# give agents real capabilities.
TOOL_HANDLERS: Dict[str, ToolHandler] = {}


def _accepts_sampling_params(model: str) -> bool:
    """Return True if the model accepts temperature/top_p (older Claude models)."""
    return not any(model.startswith(prefix) for prefix in _NO_SAMPLING_PARAM_PREFIXES)


class AgentRuntime:
    """Executes agent tasks via the Anthropic SDK tool-use loop."""

    # Maps the application's agent types to a short role descriptor that is
    # prepended to the agent's own system prompt.
    _ROLE_BY_TYPE = {
        AgentType.CONVERSATIONAL: "a conversational customer support specialist",
        AgentType.ANALYTICAL: "a data analyst and researcher",
        AgentType.CREATIVE: "a creative content writer",
        AgentType.AUTOMATION: "an automation and workflow specialist",
    }

    # ------------------------------------------------------------------ #
    # Configuration helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _role_for(agent: Agent) -> str:
        return AgentRuntime._ROLE_BY_TYPE.get(agent.agent_type, "a general-purpose assistant")

    @staticmethod
    def _build_system_prompt(agent: Agent) -> str:
        """Compose the system prompt from the agent's role and configured prompt."""
        role = AgentRuntime._role_for(agent)
        base = agent.system_prompt or ""
        # Validate/sanitize the operator-provided system prompt.
        safe_prompt = PromptSanitizer.validate_agent_prompt(base) if base else ""
        header = f"You are {role}."
        if safe_prompt:
            return f"{header}\n\n{safe_prompt}"
        return header

    @staticmethod
    def build_tools(agent: Agent) -> List[Dict[str, Any]]:
        """
        Build the Anthropic tool schema list for an agent.

        Returns an empty list today (no tools wired up). To add a tool:
          1. Append its JSON-schema definition here (optionally gated on
             ``agent.tools_config``).
          2. Register an async handler in ``TOOL_HANDLERS`` under the same name.
        """
        # tools_config is reserved for per-agent tool enablement.
        return []

    @staticmethod
    def _resolve_model(
        model_string: str, validator: ModelValidator = None
    ) -> tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate the model string and return (model_id, api_key, error).

        Only the Anthropic provider is supported by this runtime. Non-Anthropic
        providers return a descriptive error rather than silently failing.

        SECURITY: API keys come ONLY from environment variables.
        """
        validator = validator or model_validator
        validation = validator.validate_model(model_string, check_configured=True)

        if not validation.is_valid:
            return None, None, {"error": validation.error}

        if validation.provider != "anthropic":
            return None, None, {
                "error": (
                    f"Provider '{validation.provider}' is not supported by the Claude "
                    f"agent runtime. Configure an Anthropic model (e.g. "
                    f"'anthropic/claude-opus-4-8')."
                )
            }

        api_key = provider_registry.get_api_key("anthropic")
        if not api_key:
            provider_config = provider_registry.get_provider("anthropic")
            env_var = provider_config.api_key_env if provider_config else "ANTHROPIC_API_KEY"
            return None, None, {
                "error": (
                    f"API key not configured for provider 'anthropic'. "
                    f"Set {env_var} (or PERSONAL_Q_API_KEY) environment variable."
                )
            }

        # validation.model is the bare model id (no provider prefix), which is
        # exactly what the Anthropic Messages API expects.
        return validation.model, api_key, None

    @staticmethod
    def _client(api_key: str) -> AsyncAnthropic:
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=TIMEOUT_CONNECT,
                read=TIMEOUT_READ,
                write=TIMEOUT_WRITE,
                pool=TIMEOUT_POOL,
            )
        )
        return AsyncAnthropic(api_key=api_key, http_client=http_client)

    # ------------------------------------------------------------------ #
    # Core agentic loop
    # ------------------------------------------------------------------ #
    @staticmethod
    @retry(
        retry=retry_if_exception_type(
            (APIConnectionError, RateLimitError, httpx.TimeoutException)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _create_message(
        client: AsyncAnthropic,
        *,
        model: str,
        max_tokens: int,
        temperature: Optional[float],
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ):
        """Single Messages API call with retry on transient errors."""
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        # Only send temperature to models that accept it.
        if temperature is not None and _accepts_sampling_params(model):
            kwargs["temperature"] = temperature
        if tools:
            kwargs["tools"] = tools
        return await client.messages.create(**kwargs)

    @staticmethod
    async def _run_loop(
        client: AsyncAnthropic,
        *,
        model: str,
        max_tokens: int,
        temperature: Optional[float],
        system: str,
        initial_user_content: str,
        tools: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Drive the agentic loop until the model stops requesting tools.

        Returns a dict with the final text, token usage, and iteration count.
        """
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": initial_user_content}
        ]
        total_input = 0
        total_output = 0

        for iteration in range(1, MAX_AGENT_ITERATIONS + 1):
            response = await AgentRuntime._create_message(
                client,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages,
                tools=tools,
            )

            if response.usage:
                total_input += response.usage.input_tokens or 0
                total_output += response.usage.output_tokens or 0

            # Server-side tools may pause; re-send to resume.
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            if response.stop_reason != "tool_use" or not tool_use_blocks:
                # Done — gather the final text.
                text = "".join(
                    block.text for block in response.content if block.type == "text"
                ).strip()
                return {
                    "text": text,
                    "usage": {"input_tokens": total_input, "output_tokens": total_output},
                    "iterations": iteration,
                    "stop_reason": response.stop_reason,
                }

            # Execute requested tools and feed the results back.
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in tool_use_blocks:
                handler = TOOL_HANDLERS.get(block.name)
                if handler is None:
                    result_content = f"Error: tool '{block.name}' is not available."
                    is_error = True
                else:
                    try:
                        result_content = await handler(block.input)
                        is_error = False
                    except Exception as exc:  # noqa: BLE001 - report tool failure to model
                        logger.warning("Tool '%s' failed: %s", block.name, exc)
                        result_content = f"Error executing tool '{block.name}': {exc}"
                        is_error = True
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_content,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        # Loop budget exhausted.
        return {
            "text": "",
            "usage": {"input_tokens": total_input, "output_tokens": total_output},
            "iterations": MAX_AGENT_ITERATIONS,
            "stop_reason": "max_iterations",
            "error": "Agent stopped after reaching the maximum number of tool iterations.",
        }

    # ------------------------------------------------------------------ #
    # Public API (matches the former CrewService surface)
    # ------------------------------------------------------------------ #
    @staticmethod
    async def execute_agent_task(
        db: AsyncSession,
        agent: Agent,
        task_description: str,
        task_input: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task with a single agent using the Claude tool-use loop.

        Args:
            db: Database session (unused today; kept for signature compatibility
                and future tool handlers that need DB access).
            agent: Agent to execute the task.
            task_description: The task prompt.
            task_input: Optional structured input merged into the prompt.

        Returns:
            Result dict: {success, result/error, agent_id, task_description,
                          model_used, usage, iterations}.
        """
        model_string = agent.model or settings.default_model
        model_id, api_key, error = AgentRuntime._resolve_model(model_string)

        if error:
            return {
                "success": False,
                "error": error["error"],
                "agent_id": agent.id,
                "task_description": task_description,
            }

        try:
            user_content = AgentRuntime._compose_task_prompt(task_description, task_input)
        except ValueError as exc:
            logger.warning("Rejected task prompt for agent '%s': %s", agent.name, exc)
            return {
                "success": False,
                "error": "Invalid task content detected.",
                "agent_id": agent.id,
                "task_description": task_description,
            }

        system = AgentRuntime._build_system_prompt(agent)
        tools = AgentRuntime.build_tools(agent)
        temperature = (
            agent.temperature
            if agent.temperature is not None
            else settings.default_temperature
        )
        max_tokens = agent.max_tokens or settings.default_max_tokens

        client = AgentRuntime._client(api_key)
        try:
            logger.info("Executing task for agent '%s' with model '%s'", agent.name, model_id)
            loop_result = await AgentRuntime._run_loop(
                client,
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                initial_user_content=user_content,
                tools=tools,
            )
        except RateLimitError as exc:
            logger.error("Rate limited executing agent task: %s", exc)
            return AgentRuntime._error_result(agent, task_description, str(exc))
        except (APIConnectionError, httpx.TimeoutException) as exc:
            logger.error("Connection/timeout executing agent task: %s", exc)
            return AgentRuntime._error_result(agent, task_description, str(exc))
        except APIError as exc:
            logger.error("Anthropic API error executing agent task: %s", exc)
            return AgentRuntime._error_result(agent, task_description, str(exc))
        except Exception as exc:  # noqa: BLE001 - surface unexpected failures
            logger.error("Task execution failed: %s", exc, exc_info=True)
            return AgentRuntime._error_result(agent, task_description, str(exc))
        finally:
            await client.close()

        if loop_result.get("error"):
            return AgentRuntime._error_result(
                agent, task_description, loop_result["error"], extra={
                    "iterations": loop_result.get("iterations"),
                }
            )

        return {
            "success": True,
            "result": loop_result["text"],
            "agent_id": agent.id,
            "task_description": task_description,
            "model_used": model_id,
            "usage": loop_result["usage"],
            "iterations": loop_result["iterations"],
        }

    @staticmethod
    async def execute_multi_agent_task(
        db: AsyncSession,
        agents: List[Agent],
        task_descriptions: List[str],
        process: str = "sequential",
    ) -> Dict[str, Any]:
        """
        Execute tasks across multiple agents.

        The agents collaborate by chaining: each agent receives the prior
        agents' outputs as context, then performs its own task. This reproduces
        CrewAI's "sequential" process. "hierarchical" currently runs the same
        sequential chain with a coordination note — true delegation can be added
        later via a delegation tool.

        Args:
            db: Database session.
            agents: Agents to run, in order.
            task_descriptions: One task per agent.
            process: "sequential" or "hierarchical".

        Returns:
            Result dict: {success, result, agents, process, model_used, usage}.
        """
        if len(agents) != len(task_descriptions):
            raise ValueError("Number of agents must match number of tasks")

        agent_summaries = [{"id": a.id, "name": a.name} for a in agents]
        transcript: List[str] = []
        total_input = 0
        total_output = 0
        last_model: Optional[str] = None

        coordination_note = (
            "You are part of a team working through tasks in sequence. "
            "Build on the prior team members' results below.\n\n"
            if process == "hierarchical"
            else ""
        )

        for agent, task_desc in zip(agents, task_descriptions):
            context = ""
            if transcript:
                context = (
                    "Results from previous team members:\n"
                    + "\n\n".join(transcript)
                    + "\n\n---\n\n"
                )
            combined = f"{coordination_note}{context}Your task: {task_desc}"

            result = await AgentRuntime.execute_agent_task(db, agent, combined)
            if not result["success"]:
                return {
                    "success": False,
                    "error": result["error"],
                    "agents": agent_summaries,
                    "process": process,
                    "failed_agent_id": agent.id,
                }

            last_model = result.get("model_used", last_model)
            usage = result.get("usage", {})
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            transcript.append(f"[{agent.name}]\n{result['result']}")

        return {
            "success": True,
            "result": transcript[-1].split("\n", 1)[-1] if transcript else "",
            "transcript": transcript,
            "agents": agent_summaries,
            "process": process,
            "model_used": last_model,
            "usage": {"input_tokens": total_input, "output_tokens": total_output},
        }

    # ------------------------------------------------------------------ #
    # Small helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _compose_task_prompt(
        task_description: str, task_input: Optional[Dict[str, Any]]
    ) -> str:
        """Sanitize and assemble the user prompt from the task and optional input."""
        safe_task = PromptSanitizer.sanitize_prompt(task_description, raise_on_detection=True)
        if task_input:
            # Render structured input as readable context.
            input_lines = "\n".join(f"- {k}: {v}" for k, v in task_input.items())
            return f"{safe_task}\n\nAdditional input:\n{input_lines}"
        return safe_task

    @staticmethod
    def _error_result(
        agent: Agent,
        task_description: str,
        error: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = {
            "success": False,
            "error": error,
            "agent_id": agent.id,
            "task_description": task_description,
        }
        if extra:
            result.update(extra)
        return result
