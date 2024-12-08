import asyncio
from uuid import uuid4

import pytest
from langchain_core.tools import StructuredTool
from langchain_core.runnables import RunnableLambda

from app.chat.local_config import LOCAL_MODELS, generation_options, resolve_model_path, truncate_at_stop
from app.chat.chat import create_models_from_config
from app.chat.local_model import LocalChatModel
from app.chat.execution import execution_events
from app.agent.agents_registry import agents_registry
from app.configs import OPENAI_PROMPT
from app.callback_handler.agent_callback_handler import AgentExecutorAsyncIteratorCallbackHandler


@pytest.mark.parametrize("name,path", LOCAL_MODELS.items())
def test_model_selection(name, path):
    assert resolve_model_path(name) == path
    assert resolve_model_path(path) == path


def test_unknown_model_fails():
    with pytest.raises(ValueError):
        resolve_model_path("unknown-model")


def test_local_factory_requires_no_weights():
    model, prompt = create_models_from_config({
        "platform": "LOCAL", "llm_model": {"Qwen2.5-72B-Instruct": {
            "temperature": 0, "max_tokens": 512
        }},
    }, callbacks=[], stream=True)
    assert isinstance(model, LocalChatModel)
    assert model.model_name == "Qwen2.5-72B-Instruct"
    assert model.max_tokens == 512
    assert "{tools}" in prompt


@pytest.mark.parametrize("temperature,tokens", [(-1, 50), (3, 50), (0.5, 0), (0.5, True), (0.5, 1.5)])
def test_invalid_generation_parameters(temperature, tokens):
    with pytest.raises(ValueError):
        generation_options(temperature, tokens)


def test_greedy_generation_and_stops():
    assert generation_options(0, 128) == {"max_new_tokens": 128, "do_sample": False}
    assert generation_options(0.7, 128)["temperature"] == 0.7
    assert truncate_at_stop("结果\nObservation: trailing", ["\nObservation:"]) == "结果"


async def test_real_tool_events_and_result():
    # 使用标准 Runnable 运算和真实工具，不调用模型服务。
    def multiply(value: int) -> str:
        return str(value * value)
    tool = StructuredTool.from_function(multiply, description="计算整数平方")
    chain = tool | RunnableLambda(lambda output: {"output": output})
    events = [event async for event in execution_events(chain, {"value": 12})]
    assert [event["type"] for event in events] == ["tool_start", "tool_end", "answer"]
    assert events[1]["text"] == "144"
    assert events[0]["run_id"] == events[1]["run_id"]
    assert events[-1]["text"] == "144"


async def test_execution_error_propagates():
    def divide(value):
        return 1 / value
    with pytest.raises(ZeroDivisionError):
        async for _ in execution_events(RunnableLambda(divide), 0):
            pass


async def test_nested_chain_does_not_end_callback():
    callback = AgentExecutorAsyncIteratorCallbackHandler()
    await callback.on_chain_end({}, run_id=uuid4(), parent_run_id=uuid4())
    assert not callback.done.is_set()
    await callback.on_tool_end("144", run_id=uuid4())
    assert "144" in callback.queue.get_nowait()


def test_local_agent_builds_without_loading_weights():
    model = LocalChatModel(model_name="Qwen2.5-72B-Instruct", cache_dir="work/cache")
    executor = agents_registry(model, tools=[], prompt=OPENAI_PROMPT)
    assert executor.tools == []
    assert executor.handle_parsing_errors is False
