"""
Unit tests for the Claude agent runtime (Anthropic SDK tool-use loop).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.models.agent import Agent, AgentStatus, AgentType
from app.schemas.llm import ValidationResult
from app.services import agent_runtime
from app.services.agent_runtime import AgentRuntime, _accepts_sampling_params


def _make_agent(**overrides) -> Agent:
    defaults = dict(
        id="agent-1",
        name="Test Agent",
        description="A test agent",
        agent_type=AgentType.ANALYTICAL,
        model="anthropic/claude-opus-4-8",
        system_prompt="You analyze data.",
        temperature=0.5,
        max_tokens=1024,
        status=AgentStatus.ACTIVE,
    )
    defaults.update(overrides)
    return Agent(**defaults)


def _text_response(text: str, *, input_tokens=10, output_tokens=5):
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def _tool_use_response(tool_id: str, name: str, tool_input: dict):
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[
            SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)
        ],
        usage=SimpleNamespace(input_tokens=8, output_tokens=4),
    )


def _patch_model_resolution(provider="anthropic", model="claude-opus-4-8", api_key="sk-test"):
    """Context managers that make _resolve_model succeed for the given provider."""
    return (
        patch(
            "app.services.agent_runtime.model_validator.validate_model",
            return_value=ValidationResult(
                is_valid=True,
                provider=provider,
                model=model,
                normalized=f"{provider}/{model}",
            ),
        ),
        patch(
            "app.services.agent_runtime.provider_registry.get_api_key",
            return_value=api_key,
        ),
    )


class TestHelpers:
    def test_role_mapping(self):
        assert "analyst" in AgentRuntime._role_for(_make_agent()).lower()
        assert "support" in AgentRuntime._role_for(
            _make_agent(agent_type=AgentType.CONVERSATIONAL)
        ).lower()

    def test_system_prompt_includes_role_and_prompt(self):
        prompt = AgentRuntime._build_system_prompt(_make_agent())
        assert "analyst" in prompt.lower()
        assert "You analyze data." in prompt

    def test_build_tools_empty_by_default(self):
        assert AgentRuntime.build_tools(_make_agent()) == []

    def test_accepts_sampling_params(self):
        # Modern models reject temperature/top_p
        assert _accepts_sampling_params("claude-opus-4-8") is False
        assert _accepts_sampling_params("claude-sonnet-4-6") is False
        assert _accepts_sampling_params("claude-fable-5") is False
        # Legacy models accept them
        assert _accepts_sampling_params("claude-sonnet-4-20250514") is True
        assert _accepts_sampling_params("claude-3-haiku-20240307") is True


class TestResolveModel:
    def test_rejects_non_anthropic_provider(self):
        validate, _ = _patch_model_resolution(provider="openai", model="gpt-4o")
        with validate:
            model_id, api_key, error = AgentRuntime._resolve_model("openai/gpt-4o")
        assert model_id is None
        assert error is not None
        assert "not supported" in error["error"].lower()

    def test_returns_bare_model_id_for_anthropic(self):
        validate, key = _patch_model_resolution()
        with validate, key:
            model_id, api_key, error = AgentRuntime._resolve_model("anthropic/claude-opus-4-8")
        assert error is None
        assert model_id == "claude-opus-4-8"
        assert api_key == "sk-test"


class TestExecuteAgentTask:
    @pytest.mark.asyncio
    async def test_happy_path_single_call(self):
        validate, key = _patch_model_resolution()
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=_text_response("The answer is 42."))
        mock_client.close = AsyncMock()

        with validate, key, patch.object(
            agent_runtime, "AsyncAnthropic", return_value=mock_client
        ):
            result = await AgentRuntime.execute_agent_task(
                db=Mock(), agent=_make_agent(), task_description="What is the answer?"
            )

        assert result["success"] is True
        assert result["result"] == "The answer is 42."
        assert result["model_used"] == "claude-opus-4-8"
        assert result["iterations"] == 1
        assert result["usage"]["input_tokens"] == 10

    @pytest.mark.asyncio
    async def test_omits_temperature_for_modern_models(self):
        validate, key = _patch_model_resolution()
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=_text_response("ok"))
        mock_client.close = AsyncMock()

        with validate, key, patch.object(
            agent_runtime, "AsyncAnthropic", return_value=mock_client
        ):
            await AgentRuntime.execute_agent_task(
                db=Mock(), agent=_make_agent(), task_description="hi"
            )

        _, kwargs = mock_client.messages.create.call_args
        assert "temperature" not in kwargs  # opus-4-8 rejects it

    @pytest.mark.asyncio
    async def test_includes_temperature_for_legacy_models(self):
        validate, key = _patch_model_resolution(model="claude-sonnet-4-20250514")
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=_text_response("ok"))
        mock_client.close = AsyncMock()

        agent = _make_agent(model="anthropic/claude-sonnet-4-20250514", temperature=0.3)
        with validate, key, patch.object(
            agent_runtime, "AsyncAnthropic", return_value=mock_client
        ):
            await AgentRuntime.execute_agent_task(
                db=Mock(), agent=agent, task_description="hi"
            )

        _, kwargs = mock_client.messages.create.call_args
        assert kwargs.get("temperature") == 0.3

    @pytest.mark.asyncio
    async def test_tool_use_loop(self):
        validate, key = _patch_model_resolution()
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response("tu-1", "echo", {"value": "hello"}),
                _text_response("Tool said: hello"),
            ]
        )
        mock_client.close = AsyncMock()

        handler = AsyncMock(return_value="hello")

        with validate, key, patch.object(
            agent_runtime, "AsyncAnthropic", return_value=mock_client
        ), patch.object(
            AgentRuntime,
            "build_tools",
            return_value=[{"name": "echo", "description": "echo", "input_schema": {}}],
        ), patch.dict(agent_runtime.TOOL_HANDLERS, {"echo": handler}, clear=False):
            result = await AgentRuntime.execute_agent_task(
                db=Mock(), agent=_make_agent(), task_description="use the echo tool"
            )

        assert result["success"] is True
        assert result["result"] == "Tool said: hello"
        assert result["iterations"] == 2
        handler.assert_awaited_once_with({"value": "hello"})

    @pytest.mark.asyncio
    async def test_unknown_tool_reports_error_to_model(self):
        validate, key = _patch_model_resolution()
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response("tu-1", "missing_tool", {}),
                _text_response("Recovered without the tool."),
            ]
        )
        mock_client.close = AsyncMock()

        with validate, key, patch.object(
            agent_runtime, "AsyncAnthropic", return_value=mock_client
        ), patch.object(
            AgentRuntime,
            "build_tools",
            return_value=[{"name": "missing_tool", "description": "x", "input_schema": {}}],
        ):
            result = await AgentRuntime.execute_agent_task(
                db=Mock(), agent=_make_agent(), task_description="try a tool"
            )

        assert result["success"] is True
        # Second call's messages should contain a tool_result flagged as error.
        second_call_kwargs = mock_client.messages.create.call_args_list[1].kwargs
        tool_result_msg = second_call_kwargs["messages"][-1]
        assert tool_result_msg["content"][0]["is_error"] is True


class TestMultiAgentTask:
    @pytest.mark.asyncio
    async def test_task_count_mismatch_raises(self):
        with pytest.raises(ValueError, match="must match"):
            await AgentRuntime.execute_multi_agent_task(
                db=Mock(),
                agents=[_make_agent()],
                task_descriptions=["a", "b"],
            )

    @pytest.mark.asyncio
    async def test_sequential_chaining(self):
        agents = [
            _make_agent(id="a1", name="Researcher"),
            _make_agent(id="a2", name="Writer"),
        ]

        async def fake_execute(db, agent, task_description, task_input=None):
            return {
                "success": True,
                "result": f"{agent.name} output",
                "agent_id": agent.id,
                "task_description": task_description,
                "model_used": "claude-opus-4-8",
                "usage": {"input_tokens": 5, "output_tokens": 3},
                "iterations": 1,
            }

        with patch.object(AgentRuntime, "execute_agent_task", side_effect=fake_execute):
            result = await AgentRuntime.execute_multi_agent_task(
                db=Mock(),
                agents=agents,
                task_descriptions=["research", "write"],
                process="sequential",
            )

        assert result["success"] is True
        assert len(result["transcript"]) == 2
        assert result["usage"]["input_tokens"] == 10
        assert result["process"] == "sequential"
