import json
from contextlib import closing
from datetime import datetime
from uuid import uuid4

from fastapi import Body, HTTPException

from ..chat.execution import run_chat
from ..chat.utils import History
from ..model_configs.utils import get_config_from_id
from ..utils.system_utils import BaseResponse, ListResponse, get_mindpilot_db_connection
from .message import init_messages_table
from .streaming import event_message


def init_conversations_table():
    with closing(get_mindpilot_db_connection()) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS conversations (conversation_id TEXT PRIMARY KEY, "
            "title TEXT, created_at TEXT, updated_at TEXT, is_summarized BOOLEAN, agent_id INTEGER)"
        )


async def add_conversation(agent_id: int = Body(0)):
    init_conversations_table()
    init_messages_table()
    conversation_id = str(uuid4())
    timestamp = datetime.now().isoformat()
    with closing(get_mindpilot_db_connection()) as connection, connection:
        connection.execute(
            "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, "New Conversation", timestamp, timestamp, False, agent_id),
        )
    return BaseResponse(code=200, msg="success", data={
        "conversation_id": conversation_id, "title": "New Conversation",
        "created_at": timestamp, "updated_at": timestamp,
        "is_summarized": False, "agent_id": agent_id,
    })


async def list_conversations():
    init_conversations_table()
    init_messages_table()
    with closing(get_mindpilot_db_connection()) as connection:
        rows = connection.execute("SELECT * FROM conversations ORDER BY created_at").fetchall()
    return ListResponse(code=200, msg="success", data=[dict(row) for row in rows])


async def get_conversation(conversation_id: str):
    init_conversations_table()
    init_messages_table()
    with closing(get_mindpilot_db_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()
        if row is None:
            return BaseResponse(code=404, msg="Conversation not found")
        conversation = dict(row)
        messages = connection.execute(
            "SELECT id, agent_status, role, content, files, timestamp FROM message "
            "WHERE conversation_id = ? ORDER BY id", (conversation_id,)
        ).fetchall()
    conversation["messages"] = [{
        "message_id": message["id"], "agent_status": message["agent_status"],
        "role": message["role"], "text": message["content"],
        "files": json.loads(message["files"]), "timestamp": message["timestamp"],
    } for message in messages]
    return BaseResponse(code=200, msg="success", data=conversation)


async def delete_conversation(conversation_id: str):
    init_conversations_table()
    init_messages_table()
    with closing(get_mindpilot_db_connection()) as connection, connection:
        exists = connection.execute(
            "SELECT 1 FROM conversations WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()
        if exists is None:
            return BaseResponse(code=404, msg="Conversation not found")
        connection.execute("DELETE FROM message WHERE conversation_id = ?", (conversation_id,))
        connection.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
    return BaseResponse(code=200, msg="success", data={"conversation_id": conversation_id})


async def debug_messages(
    query: str = Body(...), history: list[History] = Body(default=[]),
    config_id: int = Body(...), agent_config: dict = Body(...),
):
    config = get_config_from_id(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    params = next(iter(config["llm_model"].values()))
    params["temperature"] = agent_config["temperature"]
    params["max_tokens"] = agent_config["max_tokens"]
    messages = []
    async for event in run_chat(
        query, [History.from_data(item).model_dump() for item in history], config,
        0 if agent_config["agent_enable"] else -1,
        agent_config.get("tool_config", []), agent_config=agent_config,
    ):
        message = event_message(event)
        if message:
            status, text = message
            messages.append({"message_id": len(messages), "agent_status": status,
                             "text": text, "files": [], "timestamp": datetime.now().isoformat()})
    return BaseResponse(code=200, msg="success", data=messages)
