import json
import re
from typing import List

from fastapi import Body
from uuid import uuid4
from datetime import datetime
import sqlite3

from ..chat.utils import History
from ..utils.system_utils import BaseResponse, ListResponse, get_mindpilot_db_connection
from .message import init_messages_table, insert_message, split_message_content
from ..model_configs.utils import get_config_from_id
from ..agent.utils import get_agent_from_id
from ..chat.chat import chat_online, debug_chat_online


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
            "text": row['content'],
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
        text: str = Body("", description="消息内容"),
        tool_config: List[str] = Body([], description="工具配置", examples=[]),
        temperature: float = Body(..., description="模型温度", examples=[0.8]),
        max_tokens: int = Body(..., description="模型输出最大长度", examples=[4096]),

):
    # TODO 缺少知识库部分
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

    # print(history)

    # 存放用户输入
    _, timestamp_user = insert_message(agent_status=0, role=role, content=text, files=json.dumps(files),
                                       conversation_id=conversation_id)

    cursor.execute('''
            UPDATE conversations
            SET updated_at = ?
            WHERE conversation_id = ?
        ''', (timestamp_user, conversation_id))
    conn.commit()

    # 获取模型配置
    chat_model_config = get_config_from_id(config_id=config_id)
    model_key = next(iter(chat_model_config["llm_model"]))
    chat_model_config["llm_model"][model_key]["temperature"] = temperature
    chat_model_config["llm_model"][model_key]["max_tokens"] = max_tokens

    is_summery = False

    if agent_id == -1:
        cursor.execute('''SELECT agent_id FROM conversations WHERE conversation_id = ?''', (conversation_id,))
        temp_agent_id = cursor.fetchone()[0]
        if temp_agent_id != -1:
            temp_agent = get_agent_from_id(temp_agent_id)
            temp_agent_name = temp_agent["agent_name"]
            temp_agent_abstract = temp_agent["agent_abstract"]
            temp_agent_info = temp_agent["agent_info"]
            agent_prompt = "Your name is " + temp_agent_name + "." + temp_agent_abstract + ". Below is your detailed information:" + temp_agent_info + "."
            history.append({"role": "user", "content": agent_prompt})
            is_summery = True

    if len(history) == 0 or is_summery == True:
        if len(history) == 0:
            summery_prompt = "下面是用户的问题，请总结为不超过八个字的标题。\n" + "用户：" + text + '输出格式为：{"title":"总结的标题"}，除了这个json，不允许输出其他内容。'
        if is_summery == True:
            summery_prompt = "下面是用户的问题，请总结为不超过八个字的标题。\n" + "用户：" + agent_prompt + text + '输出格式为：{"title":"总结的标题"}，除了这个json，不允许输出其他内容。'
        summery = await chat_online(content=summery_prompt, history=[], chat_model_config=chat_model_config,
                                    agent_id=-1, tool_config=tool_config, conversation_id=conversation_id)
        summery_content = summery[0]['choices'][0]['delta']['content']
        try:
            summery_content = json.loads(summery_content)["title"]
            cursor.execute('''
                    UPDATE conversations
                    SET is_summarized = ?, title = ?
                    WHERE conversation_id = ?
                ''', (True, summery_content, conversation_id))
            conn.commit()
        except Exception as e:
            print(e)

    # 获取模型输出
    ret = await chat_online(content=text, history=history, chat_model_config=chat_model_config,
                            tool_config=tool_config, agent_id=agent_id, conversation_id=conversation_id)

    response_messages = []
    for message in ret:
        if message['status'] == 7:
            message_role = message['choices'][0]['role']
            message_content = "Observation:\n" + message['choices'][0]['delta']['tool_calls'][0]['tool_output']
            message_id, timestamp_message = insert_message(agent_status=7, role=message_role, content=message_content,
                                                           files=json.dumps({}), conversation_id=conversation_id)

            cursor.execute('''
                    UPDATE conversations
                    SET updated_at = ?
                    WHERE conversation_id = ?
                ''', (timestamp_message, conversation_id))
            conn.commit()

            message_dict = {
                "message_id": message_id,
                "agent_status": 7,
                "text": message_content,
                "files": [],
                "timestamp": timestamp_message
            }
            response_messages.append(message_dict)

        if message['status'] == 3:
            message_role = message['choices'][0]['role']
            message_content = message['choices'][0]['delta']['content']
            message_list = split_message_content(message_content)
            for m in message_list:
                message_id, timestamp_message = insert_message(agent_status=3, role=message_role, content=m,
                                                               files=json.dumps({}), conversation_id=conversation_id)

                cursor.execute('''
                        UPDATE conversations
                        SET updated_at = ?
                        WHERE conversation_id = ?
                    ''', (timestamp_message, conversation_id))
                conn.commit()

                message_dict = {
                    "message_id": message_id,
                    "agent_status": 3,
                    "text": m,
                    "files": [],
                    "timestamp": timestamp_message
                }

                response_messages.append(message_dict)

        # TODO 这里考虑处理一下message['status']是4但之前一个message['status']不是3的，即agent无法解析的内容

    conn.close()

    return BaseResponse(code=200, msg="success", data=response_messages)


async def debug_messages(
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
        config_id: int = Body("0", description="模型配置", examples=[1]),
        agent_config: dict = Body(..., description="agent配置", examples=[
            {
                "agent_name": "调试助手",
                "agent_abstract": "",
                "agent_info": "这是一个用于调试的AI助手",
                "agent_enable": True,
                "temperature": 0.7,
                "max_tokens": 150,
                "tool_config": ["search_internet", "calculator"]
            }
        ])
):
    # TODO 缺少知识库部分

    if not agent_config["agent_enable"]:
        temp_agent_name = agent_config["agent_name"]
        temp_agent_abstract = agent_config["agent_abstract"]
        temp_agent_info = agent_config["agent_info"]
        agent_prompt = "Your name is " + temp_agent_name + "." + temp_agent_abstract + ". Below is your detailed information:" + temp_agent_info + "."
        history.append({"role": "user", "content": agent_prompt})

    # 获取模型配置
    chat_model_config = get_config_from_id(config_id=config_id)
    model_key = next(iter(chat_model_config["llm_model"]))
    chat_model_config["llm_model"][model_key]["temperature"] = agent_config['temperature']
    chat_model_config["llm_model"][model_key]["max_tokens"] = agent_config['max_tokens']

    # 获取模型输出
    ret = await debug_chat_online(content=query, history=history, chat_model_config=chat_model_config,
                                  tool_config=agent_config['tool_config'], agent_config=agent_config)

    response_messages = []
    for message in ret:
        if message['status'] == 7:
            message_role = message['choices'][0]['role']
            message_content = "Observation:\n" + message['choices'][0]['delta']['tool_calls'][0]['tool_output']
            timestamp = datetime.now().isoformat()
            message_dict = {
                "message_id": 0,
                "agent_status": 7,
                "text": message_content,
                "files": [],
                "timestamp": timestamp
            }
            response_messages.append(message_dict)

        if message['status'] == 3:
            message_role = message['choices'][0]['role']
            message_content = message['choices'][0]['delta']['content']
            message_list = split_message_content(message_content)
            for m in message_list:
                timestamp = datetime.now().isoformat()
                message_dict = {
                    "message_id": 0,
                    "agent_status": 3,
                    "text": m,
                    "files": [],
                    "timestamp": timestamp
                }

                response_messages.append(message_dict)

        # TODO 这里考虑处理一下message['status']是4但之前一个message['status']不是3的，即agent无法解析的内容

    return BaseResponse(code=200, msg="success", data=response_messages)