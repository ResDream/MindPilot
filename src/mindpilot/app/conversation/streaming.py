import asyncio
import json
import sqlite3
from contextlib import closing
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..chat.execution import run_chat
from ..chat.local_config import resolve_model_path


class MessageRequest(BaseModel):
    role: str = "user"
    agent_id: int = -1
    config_id: int
    text: str = Field(min_length=1)
    files: dict = Field(default_factory=dict)
    tool_config: list[str] = Field(default_factory=list)
    temperature: float = Field(default=0.8, ge=0, le=2)
    max_tokens: int = Field(default=4096, gt=0, strict=True)


class ConversationStore:
    def __init__(self, path):
        self.path = path

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def prepare(self, conversation_id: str, request: MessageRequest):
        if request.role != "user" or not request.text.strip():
            raise ValueError("请输入用户消息")
        with closing(self.connect()) as connection:
            conversation = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if conversation is None:
                raise LookupError("会话不存在")
            config = connection.execute(
                "SELECT * FROM model_configs WHERE id = ?", (request.config_id,)
            ).fetchone()
            if config is None:
                raise LookupError("模型配置不存在")
            history = [dict(row) for row in connection.execute(
                "SELECT role, content FROM message WHERE conversation_id = ? "
                "AND (role = ? OR agent_status IN (-1, 3, 5)) ORDER BY id",
                (conversation_id, "user"),
            )]
            history = conversation_history(history)
            model_config = {
                "platform": config["platform"], "base_url": config["base_url"],
                "api_key": config["api_key"], "llm_model": {config["model"]: {
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens, "callbacks": True,
                }},
            }
        return history, model_config

    def save(self, conversation_id, status, text, role="assistant", files=None):
        timestamp = datetime.now().isoformat()
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO message (agent_status, role, content, files, timestamp, conversation_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (status, role, text, json.dumps(files or {}, ensure_ascii=False), timestamp, conversation_id),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (timestamp, conversation_id),
            )
            if role == "user":
                connection.execute(
                    "UPDATE conversations SET title = ?, is_summarized = 1 "
                    "WHERE conversation_id = ? AND is_summarized = 0",
                    (text.strip()[:24], conversation_id),
                )
            return {"message_id": cursor.lastrowid, "agent_status": status,
                    "text": text, "files": files or {}, "timestamp": timestamp}


def event_message(event):
    kind = event["type"]
    if kind == "tool_start":
        return 3, json.dumps({"action": event["name"],
                              "action_input": event["input"]}, ensure_ascii=False)
    if kind == "tool_end":
        return 7, "Observation:\n" + event["text"]
    if kind == "answer":
        return -1, event["text"]
    return None


def conversation_history(messages):
    history = []
    for message in messages:
        content = message["content"]
        if message["role"] == "assistant":
            candidate = content.strip()
            if candidate.startswith("```json") and candidate.endswith("```"):
                candidate = candidate[7:-3].strip()
            if candidate.startswith("{"):
                try:
                    action = json.loads(candidate)
                except json.JSONDecodeError:
                    action = None
                if isinstance(action, dict) and "action" in action:
                    if action["action"] != "Final Answer":
                        continue
                    content = str(action["action_input"])
        history.append({"role": message["role"], "content": content})
    return history


_active_conversations = set()


async def conversation_events(store, conversation_id, request, history, config):
    if conversation_id in _active_conversations:
        raise ValueError("当前会话正在执行任务")
    _active_conversations.add(conversation_id)
    try:
        store.save(conversation_id, 0, request.text, role="user", files=request.files)
        yield {"type": "started"}
        async for event in run_chat(request.text, history, config, request.agent_id, request.tool_config):
            message = event_message(event)
            if message:
                event["message"] = store.save(conversation_id, *message)
            yield event
        yield {"type": "done"}
    finally:
        _active_conversations.remove(conversation_id)


def prepare_request(conversation_id, request):
    from ..utils.system_utils import get_resource_path
    store = ConversationStore(get_resource_path("mindpilot.db"))
    if conversation_id in _active_conversations:
        raise HTTPException(status_code=409, detail="当前会话正在执行任务")
    try:
        history, config = store.prepare(conversation_id, request)
        if config["platform"] == "LOCAL":
            resolve_model_path(next(iter(config["llm_model"])))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return store, history, config


async def send_messages(conversation_id: str, request: MessageRequest):
    store, history, config = prepare_request(conversation_id, request)
    messages = []
    async for event in conversation_events(store, conversation_id, request, history, config):
        if "message" in event:
            messages.append(event["message"])
    return {"code": 200, "msg": "success", "data": messages}


async def stream_messages(conversation_id: str, request: MessageRequest):
    store, history, config = prepare_request(conversation_id, request)

    async def stream():
        try:
            async for event in conversation_events(store, conversation_id, request, history, config):
                yield {"event": "message", "data": json.dumps(event, ensure_ascii=False)}
        except asyncio.CancelledError:
            raise
        except Exception as error:
            # SSE 已发送响应头，通过错误事件把执行失败传递给界面。
            yield {"event": "message", "data": json.dumps(
                {"type": "error", "text": str(error)}, ensure_ascii=False
            )}
            raise

    return EventSourceResponse(stream(), ping=15)
