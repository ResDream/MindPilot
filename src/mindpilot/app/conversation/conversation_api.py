import json
from typing import List

from fastapi import Body
from uuid import uuid4
from datetime import datetime
import sqlite3
from ..utils.system_utils import BaseResponse, ListResponse, get_mindpilot_db_connection
from .message import init_messages_table, insert_message
from ..model_configs.utils import get_config_from_id
from ..agent.utils import get_agent_from_id
from ..chat.chat import chat_online


def init_conversations_table():
    conn = get_mindpilot_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_summarized BOOLEAN,
            agent_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()


async def add_conversation(
        agent_id: int = Body(0, description="使用agent情况,-1代表不使用agent,0代表使用默认agent"),
):
    init_conversations_table()
    init_messages_table()
    conversation_id = str(uuid4())
    created_at = updated_at = datetime.now().isoformat()
    is_summarized = False

    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (conversation_id, title, created_at, updated_at, is_summarized, agent_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (conversation_id, "New Conversation", created_at, updated_at, is_summarized, agent_id))
    conn.commit()
    conn.close()

    response_data = {
        "conversation_id": conversation_id,
        "title": "New Conversation",
        "created_at": datetime.fromisoformat(created_at),
        "updated_at": datetime.fromisoformat(updated_at),
        "is_summarized": is_summarized,
        "agent_id": agent_id,
    }
    return BaseResponse(code=200, msg="success", data=response_data)


async def list_conversations():
    init_conversations_table()
    init_messages_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT conversation_id, title, created_at, updated_at, is_summarized, agent_id
        FROM conversations
    ''')
    rows = cursor.fetchall()
    conn.close()

    conversations = []
    for row in rows:
        conversation = {
            "conversation_id": row['conversation_id'],
            "title": row['title'],
            "created_at": datetime.fromisoformat(row['created_at']),
            "updated_at": datetime.fromisoformat(row['updated_at']),
            "is_summarized": row['is_summarized'],
            "agent_id": row['agent_id'],
        }
        conversations.append(conversation)

    return ListResponse(code=200, msg="success", data=conversations)


async def get_conversation(conversation_id: str):
    init_conversations_table()
    init_messages_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    # 获取对话详情
    cursor.execute('''
        SELECT conversation_id, title, created_at, updated_at, is_summarized, agent_id
        FROM conversations
        WHERE conversation_id = ?
    ''', (conversation_id,))
    conversation_row = cursor.fetchone()

    if not conversation_row:
        conn.close()
        return BaseResponse(code=404, msg="Conversation not found")

    conversation = {
        "conversation_id": conversation_row['conversation_id'],
        "title": conversation_row['title'],
        "created_at": datetime.fromisoformat(conversation_row['created_at']),
        "updated_at": datetime.fromisoformat(conversation_row['updated_at']),
        "is_summarized": conversation_row['is_summarized'],
        "agent_id": conversation_row['agent_id'],
        "messages": []
    }

    # 获取对话的所有消息
    cursor.execute('''
        SELECT id, agent_status, role, content, files, timestamp
        FROM message
        WHERE conversation_id = ?
    ''', (conversation_id,))
    message_rows = cursor.fetchall()

    for row in message_rows:
        message = {
            "message_id": row['id'],
            "agent_status": row['agent_status'],
            "role": row['role'],
            "content": row['content'],
            "files": json.loads(row['files']),
            "timestamp": datetime.fromisoformat(row['timestamp'])
        }
        conversation['messages'].append(message)

    conn.close()

    return BaseResponse(code=200, msg="success", data=conversation)


async def delete_conversation(conversation_id: str):
    init_conversations_table()
    init_messages_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    # 检查对话是否存在
    cursor.execute('''
        SELECT conversation_id
        FROM conversations
        WHERE conversation_id = ?
    ''', (conversation_id,))
    conversation_row = cursor.fetchone()

    if not conversation_row:
        conn.close()
        return BaseResponse(code=404, msg="Conversation not found", data={"conversation_id": "-1"})

    # 删除对话相关的消息
    cursor.execute('''
        DELETE FROM message
        WHERE conversation_id = ?
    ''', (conversation_id,))

    # 删除对话
    cursor.execute('''
        DELETE FROM conversations
        WHERE conversation_id = ?
    ''', (conversation_id,))

    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg="success", data={"conversation_id": conversation_id})


async def send_messages(
        conversation_id: str,
        role: str = Body("", description="消息角色：user/assistant", examples=["user", "assistant"]),
        agent_id: int = Body(0, description="使用agent,0为默认,-1为不使用agent", examples=[0]),
        config_id: int = Body("0", description="模型配置", examples=[1]),
        files: dict = Body({}, description="文件", examples=[{}]),
        content: str = Body("", description="消息内容"),
        tool_config: List[str] = Body([], description="工具配置", examples=[]),
):
    """
        1. 获取历史记录
        2. 存放用户输入
        3. 获取模型配置
        4. 获取agent信息
        5. 组织模型输出
        6. 存放模型输出
    """
    init_conversations_table()
    init_messages_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    # 获取历史记录
    cursor.execute('''
            SELECT role, content, timestamp
            FROM message
            WHERE conversation_id = ?
            ORDER BY timestamp
        ''', (conversation_id,))
    message_rows = cursor.fetchall()

    history = []
    for row in message_rows:
        history.append({
            "role": row['role'],
            "content": row['content']
        })

    # 存放用户输入
    insert_message(agent_status=0, role=role, content=content, files=json.dumps(files), conversation_id=conversation_id,
                   tool_calls=json.dumps({}))

    # 获取模型配置
    chat_model_config = get_config_from_id(config_id=config_id)

    # 获取模型输出
    ret = await chat_online(content=content, history=history, chat_model_config=chat_model_config,
                            tool_config=tool_config, agent_id=agent_id)

    # 解析模型输出
    message_id = str(uuid4())
    message_role = ret['choices'][0]['message']['role']
    message_content = ret['choices'][0]['message']['content']
    tool_calls = ret['choices'][0]['message']['tool_calls']

    # 存放模型输出
    timestamp = insert_message(agent_status=5, role=message_role, content=message_content, files=json.dumps(files),
                               conversation_id=conversation_id, tool_calls=json.dumps(tool_calls))

    # 构建响应
    response_data = {
        "messages": [
            {
                "id": message_id,
                "role": message_role,
                "agent_status": 5,
                "content": message_content,
                "tool_calls": tool_calls,
                "files": files,
                "timestamp": datetime.fromisoformat(timestamp)
            }
        ]
    }

    conn.close()

    return BaseResponse(code=200, msg="success", data=response_data)