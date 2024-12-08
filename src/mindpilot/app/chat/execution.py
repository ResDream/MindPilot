from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable


def message_text(value) -> str:
    if isinstance(value, str):
        return value
    if hasattr(value, "content") and isinstance(value.content, str):
        return value.content
    raise TypeError("模型必须返回文本消息")


async def execution_events(chain: Runnable, inputs):
    root_id = None
    async for event in chain.astream_events(inputs, version="v2"):
        if root_id is None:
            root_id = event["run_id"]
        kind = event["event"]
        data = event["data"]
        event_id = event["run_id"]
        if kind == "on_chat_model_start":
            yield {"type": "model_start", "run_id": event_id}
        elif kind == "on_chat_model_stream":
            text = message_text(data["chunk"])
            if text:
                yield {"type": "token", "run_id": event_id, "text": text}
        elif kind == "on_chat_model_end":
            yield {"type": "model_end", "run_id": event_id,
                   "text": message_text(data["output"])}
        elif kind == "on_tool_start":
            yield {"type": "tool_start", "run_id": event_id,
                   "name": event["name"], "input": data["input"]}
        elif kind == "on_tool_end":
            output = data["output"]
            yield {"type": "tool_end", "run_id": event_id,
                   "name": event["name"], "text": str(output)}
        if event_id == root_id and kind in ("on_chain_end", "on_chat_model_end"):
            output = data["output"]
            if isinstance(output, dict):
                output = output["output"]
            yield {"type": "answer", "text": message_text(output)}


async def run_chat(content, history, config, agent_id, tool_names, agent_config=None):
    from .chat import create_models_from_config
    from ..agent.agents_registry import agents_registry
    from ..agent.utils import get_agent_from_id
    from ..utils.system_utils import get_tool

    model, prompt = create_models_from_config(config, callbacks=[], stream=True)
    messages = [
        HumanMessage(content=item["content"]) if item["role"] == "user"
        else AIMessage(content=item["content"]) for item in history
    ]
    enabled = agent_id != -1
    agent = agent_config
    if agent is None and agent_id not in (-1, 0):
        agent = get_agent_from_id(agent_id)
        if agent is None:
            raise ValueError("指定的 Agent 不存在")
    if agent is not None:
        enabled = agent.get("agent_enable", enabled)
        persona = "\n".join(agent.get(key, "") for key in (
            "agent_name", "agent_abstract", "agent_info"
        ))
        if persona.strip():
            messages.insert(0, SystemMessage(content=persona))
        if not tool_names:
            tool_names = agent.get("tool_config", [])
    if enabled:
        registry = get_tool()
        unknown = set(tool_names) - registry.keys()
        if unknown:
            raise ValueError(f"工具不存在：{sorted(unknown)}")
        tools = [registry[name] for name in tool_names]
        chain = agents_registry(llm=model, tools=tools, prompt=prompt)
        inputs = {"input": content, "chat_history": messages}
    else:
        chain = model
        inputs = [*messages, HumanMessage(content=content)]
    async for event in execution_events(chain, inputs):
        yield event
