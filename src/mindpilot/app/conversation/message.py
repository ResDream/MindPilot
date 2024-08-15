import re
from datetime import datetime
import sqlite3
import json
from ..utils.system_utils import get_mindpilot_db_connection


# 初始化数据库和表
def init_messages_table():
    conn = get_mindpilot_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_status INTEGER,
            role TEXT,
            content TEXT,
            files TEXT, --json格式
            timestamp TEXT,
            conversation_id TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
        )
    ''')
    conn.commit()
    conn.close()


def insert_message(agent_status, role, content, files, conversation_id):
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()  # 获取当前时间戳
    cursor.execute('''
        INSERT INTO message (agent_status, role, content, files, timestamp, conversation_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (agent_status, role, content, json.dumps(files), timestamp, conversation_id))
    conn.commit()

    # 获取插入行的 id
    message_id = cursor.lastrowid

    conn.close()

    return message_id, timestamp


def split_message_content(message_content):
    # 定义正则表达式匹配模式
    pattern = r'(Question:|Thought:|Action:|Observation:)(.*?)(?=(Question:|Thought:|Action:|Observation:|$))'

    # 使用正则表达式查找所有匹配的部分
    matches = re.findall(pattern, message_content, re.DOTALL)

    # 如果没有匹配到任何关键词，直接返回原文
    if not matches:
        return [message_content.strip()]

    # 创建一个列表来按顺序存储结果
    result = []

    # 遍历匹配结果，并将它们存入列表
    for match in matches:
        section = match[0].strip() + match[1].strip()  # 保留关键字和内容
        result.append(section)

    return result
