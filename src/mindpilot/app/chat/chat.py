import asyncio
import json
import uuid
from typing import AsyncIterable, List, Dict, Any

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
from ..configs import MODEL_CONFIG, TOOL_CONFIG, OPENAI_PROMPT, PROMPT_TEMPLATES
from ..utils.system_utils import get_ChatOpenAI, get_tool, wrap_done, MsgType, get_mindpilot_db_connection
from ..agent.utils import get_agent_from_id


def create_models_from_config(configs, callbacks, stream):
    configs = configs

    platform = configs["platform"]
    base_url = configs["base_url"]
    api_key = configs["api_key"]
    llm_model = configs["llm_model"]

    model_name, params = next(iter(llm_model.items()))
    callbacks = callbacks if params.get("callbacks", False) else None

    model_instance = get_ChatOpenAI(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=params.get("temperature", 0.8),
        max_tokens=params.get("max_tokens", 4096),
        callbacks=callbacks,
        streaming=stream,
    )
    model = model_instance
    prompt = OPENAI_PROMPT

    return model, prompt


def create_models_chains(
        history, prompts, models, tools, callbacks, agent_enable
):
    if history:
        history = [History.from_data(h) for h in history]
        input_msg = History(role="user", content=PROMPT_TEMPLATES["llm_model"]["with_history"]).to_msg_template(
            False
        )
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_template() for i in history] + [input_msg]
        )
    else:
        input_msg = History(role="user", content=PROMPT_TEMPLATES["llm_model"]["default"]).to_msg_template(
            False
        )
        chat_prompt = ChatPromptTemplate.from_messages([input_msg])

    llm = models
    llm.callbacks = callbacks
    chain = LLMChain(prompt=chat_prompt, llm=llm, verbose=True)

    if agent_enable:
        agent_executor = agents_registry(
            llm=llm, callbacks=callbacks, tools=tools, prompt=prompts, verbose=True
        )
        full_chain = {"input": lambda x: x["input"], "chat_history": lambda x: x["chat_history"]} | agent_executor
    else:
        chain.llm.callbacks = callbacks
        full_chain = {"input": lambda x: x["input"], "chat_history": lambda x: x["chat_history"]} | chain
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
        chat_model_config: dict = Body({}, description="LLM 模型配置", examples=[{
            "platform": "OpenAI",
            "is_openai": True,
            "base_url": "https://api.chatanywhere.tech/v1/",
            "api_key": "sk-cERDW9Fr2ujq8D2qYck9cpc9MtPytN26466bunfYXZVZWV7Y",
            "llm_model": {
                "gpt-4o-mini": {
                    "temperature": 0.8,
                    "max_tokens": 8192,
                    "callbacks": True,
                },
            }
        }]),
        tool_config: List[str] = Body([], description="工具配置", examples=[]),
        agent_enable: bool = Body(True, description="是否启用Agent"),
        agent_id: int = Body(-1, description="使用的Agent ID，默认为-1")
):
    """Agent 对话"""

    async def chat_iterator() -> AsyncIterable[OpenAIChatOutput]:
        callback = AgentExecutorAsyncIteratorCallbackHandler()
        callbacks = [callback]

        model, prompt = create_models_from_config(
            callbacks=callbacks, configs=chat_model_config, stream=stream
        )

        all_tools = get_tool().values()
        tool_configs = tool_config

        if agent_enable:
            if agent_id != -1:
                agent_dict = get_agent_from_id(agent_id)
                agent_name = agent_dict["agent_name"]
                agent_abstract = agent_dict["agent_abstract"]
                agent_info = agent_dict["agent_info"]
                if not tool_config:
                    tool_configs = agent_dict["tool_config"]
                agent_prompt_pre = "Your name is " + agent_name + "." + agent_abstract + ". Below is your detailed information:" + agent_info + "."
                agent_prompt_after = "DO NOT forget " + agent_prompt_pre
                prompt = agent_prompt_pre + prompt + agent_prompt_after
                # TODO 处理知识库
            else:
                prompt = prompt  # 默认Agent提示模板

        tool_configs = tool_configs or TOOL_CONFIG
        tools = [tool for tool in all_tools if tool.name in tool_configs]
        tools = [t.copy(update={"callbacks": callbacks}) for t in tools]

        full_chain = create_models_chains(
            prompts=prompt,
            models=model,
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
                model=model.model_name,
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
            print(data)
            if text := data["choices"][0]["delta"]["content"]:
                ret.content += text
            if data["status"] == AgentStatus.tool_end:
                ret.tool_calls += data["choices"][0]["delta"]["tool_calls"]
            ret.model = data["model"]
            ret.created = data["created"]

        return ret.model_dump()


async def chat_online(
        content: str,
        history: List[History],
        chat_model_config: dict,
        tool_config: List[str],
        agent_id: int,
        conversation_id: str
):
    async def chat_iterator() -> AsyncIterable[OpenAIChatOutput]:
        callback = AgentExecutorAsyncIteratorCallbackHandler()
        callbacks = [callback]

        model, prompt = create_models_from_config(
            callbacks=callbacks, configs=chat_model_config, stream=False
        )

        all_tools = get_tool().values()
        tool_configs = tool_config

        agent_enable = True
        if agent_id != -1:
            if agent_id != 0:
                agent_dict = get_agent_from_id(agent_id)
                agent_name = agent_dict["agent_name"]
                agent_abstract = agent_dict["agent_abstract"]
                agent_info = agent_dict["agent_info"]
                if not tool_config:
                    tool_configs = agent_dict["tool_config"]
                agent_prompt_pre = "Your name is " + agent_name + "." + agent_abstract + ". Below is your detailed information:" + agent_info + "."
                agent_prompt_after = "DO NOT forget " + agent_prompt_pre
                prompt = agent_prompt_pre + prompt + agent_prompt_after
                # TODO 处理知识库
            else:
                prompt = prompt  # 默认Agent提示模板
        else:
            agent_enable = False

        tool_configs = tool_configs or TOOL_CONFIG
        tools = [tool for tool in all_tools if tool.name in tool_configs]
        tools = [t.copy(update={"callbacks": callbacks}) for t in tools]

        full_chain = create_models_chains(
            prompts=prompt,
            models=model,
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
                        "input": content,
                        "chat_history": history_message,
                    }
                ),
                callback.done,
            )
        )

        last_tool = {}
        async for chunk in callback.aiter():
            data = json.loads(chunk)
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
                model=model.model_name,
                status=data["status"],
                message_type=data["message_type"],
            )
            yield ret.model_dump_json()

        await task

    ret = []

    async for chunk in chat_iterator():
        data = json.loads(chunk)
        # print(data)
        if data["status"] != AgentStatus.llm_start and data["status"] != AgentStatus.llm_new_token:
            ret.append(data)

    return ret


async def debug_chat_online(
        content: str,
        history: List[History],
        chat_model_config: dict,
        tool_config: List[str],
        agent_config: Dict[str, Any]
):
    async def chat_iterator() -> AsyncIterable[OpenAIChatOutput]:
        callback = AgentExecutorAsyncIteratorCallbackHandler()
        callbacks = [callback]

        model, prompt = create_models_from_config(
            callbacks=callbacks, configs=chat_model_config, stream=False
        )

        all_tools = get_tool().values()
        tool_configs = tool_config

        agent_enable = agent_config["agent_enable"]
        if agent_enable:
            agent_name = agent_config["agent_name"]
            agent_abstract = agent_config["agent_abstract"]
            agent_info = agent_config["agent_info"]
            if not tool_config:
                tool_configs = agent_config["tool_config"]
            agent_prompt_pre = "Your name is " + agent_name + "." + agent_abstract + ". Below is your detailed information:" + agent_info + "."
            agent_prompt_after = "DO NOT forget " + agent_prompt_pre
            prompt = agent_prompt_pre + prompt + agent_prompt_after
            # TODO 处理知识库

        tool_configs = tool_configs or TOOL_CONFIG
        tools = [tool for tool in all_tools if tool.name in tool_configs]
        tools = [t.copy(update={"callbacks": callbacks}) for t in tools]

        full_chain = create_models_chains(
            prompts=prompt,
            models=model,
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
                        "input": content,
                        "chat_history": history_message,
                    }
                ),
                callback.done,
            )
        )

        last_tool = {}
        async for chunk in callback.aiter():
            data = json.loads(chunk)
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
                model=model.model_name,
                status=data["status"],
                message_type=data["message_type"],
            )
            yield ret.model_dump_json()

        await task

    ret = []

    async for chunk in chat_iterator():
        data = json.loads(chunk)
        if data["status"] != AgentStatus.llm_start and data["status"] != AgentStatus.llm_new_token:
            ret.append(data)

    return ret
