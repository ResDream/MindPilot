from typing import List, Optional
from fastapi import Body, File, UploadFile
import sqlite3
from ..utils.system_utils import BaseResponse


def create_agent(
        agent_name: str = Body(..., examples=["ChatGPT Agent"]),
        agent_abstract: str = Body("", description="Agent简介。"),
        agent_info: str = Body("", description="Agent详细配置信息"),
        temperature: float = Body(0.8, description="LLM温度"),
        max_tokens: int = Body(4096, description="模型输出最大长度"),
        tool_config: List[str] = Body([], description="工具配置", examples=[["search_internet","weather_check"]]),
        # kb_files: Optional[List[UploadFile]] = File(None, description="知识库文件"),
) -> BaseResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL UNIQUE ,
        agent_abstract TEXT,
        agent_info TEXT,
        temperature REAL,
        max_tokens INTEGER,
        tool_config TEXT
    )
    ''')
    conn.commit()

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")

    cursor.execute('SELECT id FROM agents WHERE agent_name = ?', (agent_name,))
    existing_agent = cursor.fetchone()
    if existing_agent:
        return BaseResponse(code=404, msg=f"已存在同名Agent {agent_name}")

    cursor.execute('''
        INSERT INTO agents (agent_name, agent_abstract, agent_info, temperature, max_tokens, tool_config)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (agent_name, agent_abstract, agent_info, temperature, max_tokens, ','.join(tool_config)))
    conn.commit()
    conn.close()

    # TODO 处理上传的知识库文件

    return BaseResponse(code=200, msg=f"已新增Agent {agent_name}")