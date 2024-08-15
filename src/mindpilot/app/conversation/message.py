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
            tool_calls TEXT, --json格式
            files TEXT, --json格式
            timestamp TEXT,
            conversation_id TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
        )
    ''')
    conn.commit()
    conn.close()


def insert_message(agent_status, role, content, files, conversation_id, tool_calls):
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()  # 获取当前时间戳
    cursor.execute('''
        INSERT INTO message (agent_status, role, content, tool_calls, files, timestamp, conversation_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (agent_status, role, content, tool_calls, json.dumps(files), timestamp, conversation_id))
    conn.commit()
    conn.close()

    return timestamp
