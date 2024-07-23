import asyncio
import json
import uuid
from typing import AsyncIterable, List

from fastapi import Body
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, convert_to_messages
from sse_starlette.sse import EventSourceResponse

from ..agent.agents_registry import agents_registry
from ..api.api_schemas import OpenAIChatOutput
from ..callback_handler.agent_callback_handler import (
    AgentExecutorAsyncIteratorCallbackHandler,
    AgentStatus,
)
from ..chat.utils import History
from ..utils import (
    MsgType,
    get_ChatOpenAI,
    get_prompt_template,
    get_tool,
    wrap_done,
)
from app.configs import MODEL_CONFIG,TOOL_CONFIG


def create_models_from_config(configs, callbacks, stream):
    configs = configs or MODEL_CONFIG
    models = {}
    prompts = {}
    for model_type, model_configs in configs.items():
        for model_name, params in model_configs.items():
            callbacks = callbacks if params.get("callbacks", False) else None
            model_instance = get_ChatOpenAI(
                model_name=model_name,
                temperature=params.get("temperature", 0.8),
                max_tokens=params.get("max_tokens", 5000),
                callbacks=callbacks,
                streaming=stream,
            )
            models[model_type] = model_instance
            prompt_name = params.get("prompt_name", "default")
            prompt_template = get_prompt_template(type=model_type, name=prompt_name)
            prompts[model_type] = prompt_template
    return models, prompts


def create_models_chains(
    history, prompts, models, tools, callbacks, agent_enable
):
    chat_prompt = None

    if history:
        history = [History.from_data(h) for h in history]
        input_msg = History(role="user", content=prompts["llm_model"]).to_msg_template(
            False
        )
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_template() for i in history] + [input_msg]
        )
    else:
        input_msg = History(role="user", content=prompts["llm_model"]).to_msg_template(
            False
        )
        chat_prompt = ChatPromptTemplate.from_messages([input_msg])
    print(chat_prompt)

    llm = models["llm_model"]
    llm.callbacks = callbacks
    chain = LLMChain(prompt=chat_prompt, llm=llm)

    if agent_enable:
        agent_executor = agents_registry(
            llm=llm, callbacks=callbacks, tools=tools, prompt=None, verbose=True
        )
        full_chain = {"input": lambda x: x["input"]} | agent_executor
    else:
        chain.llm.callbacks = callbacks
        full_chain = {"input": lambda x: x["input"]} | chain
    return full_chain


async def chat(
    query: str = Body(..., description="用户输入", examples=[""]),
    history: List[History] = Body(
        [],
        description="历史对话",
        examples=[
            [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "您好，我是智能Agent桌面助手MindPilot，请问有什么可以帮您？"},
            ]
        ],
    ),
    stream: bool = Body(True, description="流式输出"),
    chat_model_config: dict = Body({}, description="LLM 模型配置", examples=[]),
    tool_config: List[str] = Body([], description="工具配置", examples=[]),
    agent_enable: bool = Body(True, description="是否启用Agent")
):
    """Agent 对话"""

    async def chat_iterator() -> AsyncIterable[OpenAIChatOutput]:
        callback = AgentExecutorAsyncIteratorCallbackHandler()
        callbacks = [callback]

        models, prompts = create_models_from_config(
            callbacks=callbacks, configs=chat_model_config, stream=stream
        )
        all_tools = get_tool().values()
        tool_configs = tool_config or TOOL_CONFIG
        tools = [tool for tool in all_tools if tool.name in tool_configs]
        tools = [t.copy(update={"callbacks": callbacks}) for t in tools]
        full_chain = create_models_chains(
            prompts=prompts,
            models=models,
            tools=tools,
            callbacks=callbacks,
            history=history,
            agent_enable=agent_enable
        )

        _history = [History.from_data(h) for h in history]
        chat_history = [h.to_msg_tuple() for h in _history]

        history_message = convert_to_messages(chat_history)

        task = asyncio.create_task(
            wrap_done(
                full_chain.ainvoke(
                    {
                        "input": query,
                        "chat_history": history_message,
                    }
                ),
                callback.done,
            )
        )

        last_tool = {}
        async for chunk in callback.aiter():
            data = json.loads(chunk)
            # print("data:{}".format(data))
            data["tool_calls"] = []
            data["message_type"] = MsgType.TEXT

            if data["status"] == AgentStatus.tool_start:
                last_tool = {
                    "index": 0,
                    "id": data["run_id"],
                    "type": "function",
                    "function": {
                        "name": data["tool"],
                        "arguments": data["tool_input"],
                    },
                    "tool_output": None,
                    "is_error": False,
                }
                data["tool_calls"].append(last_tool)
            if data["status"] in [AgentStatus.tool_end]:
                last_tool.update(
                    tool_output=data["tool_output"],
                    is_error=data.get("is_error", False),
                )
                data["tool_calls"] = [last_tool]
                last_tool = {}
                try:
                    tool_output = json.loads(data["tool_output"])
                    if message_type := tool_output.get("message_type"):
                        data["message_type"] = message_type
                except:
                    ...
            elif data["status"] == AgentStatus.agent_finish:
                try:
                    tool_output = json.loads(data["text"])
                    if message_type := tool_output.get("message_type"):
                        data["message_type"] = message_type
                except:
                    ...

            ret = OpenAIChatOutput(
                id=f"chat{uuid.uuid4()}",
                object="chat.completion.chunk",
                content=data.get("text", ""),
                role="assistant",
                tool_calls=data["tool_calls"],
                model=models["llm_model"].model_name,
                status=data["status"],
                message_type=data["message_type"],
            )
            yield ret.model_dump_json()

        await task

    if stream:
        return EventSourceResponse(chat_iterator())
    else:
        ret = OpenAIChatOutput(
            id=f"chat{uuid.uuid4()}",
            object="chat.completion",
            content="",
            role="assistant",
            finish_reason="stop",
            tool_calls=[],
            status=AgentStatus.agent_finish,
            message_type=MsgType.TEXT,
        )

        async for chunk in chat_iterator():
            data = json.loads(chunk)
            if text := data["choices"][0]["delta"]["content"]:
                ret.content += text
            if data["status"] == AgentStatus.tool_end:
                ret.tool_calls += data["choices"][0]["delta"]["tool_calls"]
            ret.model = data["model"]
            ret.created = data["created"]

        return ret.model_dump()
