import json
import uuid

from fastapi import Body
from sse_starlette.sse import EventSourceResponse

from ..api.api_schemas import OpenAIChatOutput
from ..configs import CACHE_DIR, OPENAI_PROMPT
from ..utils.system_utils import get_ChatOpenAI
from .execution import run_chat
from .local_config import generation_options, resolve_model_path
from .local_model import LocalChatModel
from .utils import History


def create_models_from_config(configs, callbacks, stream):
    model_name, params = next(iter(configs["llm_model"].items()))
    temperature = params.get("temperature", 0.8)
    max_tokens = params.get("max_tokens", 4096)
    generation_options(temperature, max_tokens)
    if configs["platform"] == "LOCAL":
        resolve_model_path(model_name)
        model = LocalChatModel(
            model_name=model_name, cache_dir=str(CACHE_DIR),
            temperature=temperature, max_tokens=max_tokens, callbacks=callbacks,
        )
    else:
        model = get_ChatOpenAI(
            model_name=model_name, base_url=configs["base_url"], api_key=configs["api_key"],
            temperature=temperature, max_tokens=max_tokens,
            callbacks=callbacks, streaming=stream,
        )
    return model, OPENAI_PROMPT


async def chat(
    query: str = Body(...), history: list[History] = Body(default=[]),
    stream: bool = Body(True), chat_model_config: dict = Body(...),
    tool_config: list[str] = Body(default=[]), agent_enable: bool = Body(True),
    agent_id: int = Body(-1),
):
    selected_agent = (0 if agent_id == -1 else agent_id) if agent_enable else -1

    async def chunks():
        async for event in run_chat(
            query, [History.from_data(item).model_dump() for item in history],
            chat_model_config, selected_agent, tool_config,
        ):
            status = {"model_start": 1, "token": 2, "model_end": 3,
                      "answer": 5, "tool_start": 6, "tool_end": 7}[event["type"]]
            tool_calls = []
            if event["type"] in ("tool_start", "tool_end"):
                tool_calls.append({"id": event["run_id"], "type": "function",
                                   "function": {"name": event["name"],
                                                "arguments": event.get("input", {})},
                                   "tool_output": event.get("text")})
            yield OpenAIChatOutput(
                id=f"chat{uuid.uuid4()}", content=event.get("text", ""),
                model=next(iter(chat_model_config["llm_model"])), status=status, tool_calls=tool_calls,
            ).model_dump()

    if stream:
        async def events():
            async for chunk in chunks():
                yield json.dumps(chunk, ensure_ascii=False)
        return EventSourceResponse(events())

    result = OpenAIChatOutput(id=f"chat{uuid.uuid4()}", object="chat.completion",
                              content="", status=5, finish_reason="stop")
    async for chunk in chunks():
        if chunk["status"] == 5:
            result.content = chunk["choices"][0]["delta"]["content"]
    return result.model_dump()
