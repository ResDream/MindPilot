from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Request
from langchain.prompts.prompt import PromptTemplate

# from app.api.api_schemas import MsgType, OpenAIChatInput
from ..chat.chat import chat
from ..utils import (
    get_OpenAIClient,
    get_prompt_template,
    get_tool,
    get_tool_config,
)

from .openai_routes import openai_request

chat_router = APIRouter(prefix="/chat", tags=["MindPilot对话"])

chat_router.post(
    "/chat",
    summary="与llm模型对话",
)(chat)

# 定义全局model信息，用于给Text2Sql中的get_ChatOpenAI提供model_name
global_model_name = None


# @chat_router.post("/chat/completions", summary="兼容 openai 的统一 chat 接口")
# async def chat_completions(
#     request: Request,
#     body: OpenAIChatInput,
# ) -> Dict:
#     """
#     请求参数与 openai.chat.completions.create 一致，可以通过 extra_body 传入额外参数
#     tools 和 tool_choice 可以直接传工具名称，会根据项目里包含的 tools 进行转换
#     通过不同的参数组合调用不同的 chat 功能：
#     - tool_choice
#         - extra_body 中包含 tool_input: 直接调用 tool_choice(tool_input)
#         - extra_body 中不包含 tool_input: 通过 agent 调用 tool_choice
#     - tools: agent 对话
#     - 其它：LLM 对话
#     返回与 openai 兼容的 Dict
#     """
#     client = get_OpenAIClient(model_name=body.model, is_async=True)
#     extra = {**body.model_extra} or {}
#     for key in list(extra):
#         delattr(body, key)
#
#     global global_model_name
#     global_model_name = body.model
#
#     if isinstance(body.tools, list):
#         for i in range(len(body.tools)):
#             if isinstance(body.tools[i], str):
#                 if t := get_tool(body.tools[i]):
#                     body.tools[i] = {
#                         "type": "function",
#                         "function": {
#                             "name": t.name,
#                             "description": t.description,
#                             "parameters": t.args,
#                         },
#                     }
#     # agent chat with tool calls
#     if body.tools:
#         chat_model_config = {}
#         tool_names = [x["function"]["name"] for x in body.tools]
#         tool_config = {name: get_tool_config(name) for name in tool_names}
#         # print(tool_config)
#         result = await chat(
#             query=body.messages[-1]["content"],
#             # query="查询北京的天气状况，并搜索互联网给出北京的旅游攻略",
#             metadata=extra.get("metadata", {}),
#             conversation_id=extra.get("conversation_id", ""),
#             # message_id=message_id,
#             history_len=-1,
#             history=body.messages[:-1],
#             stream=body.stream,
#             chat_model_config=extra.get("chat_model_config", chat_model_config),
#             tool_config=extra.get("tool_config", tool_config),
#         )
#         return result
#     else:
#         # TODO 使用用户指定工具
#         pass
#
