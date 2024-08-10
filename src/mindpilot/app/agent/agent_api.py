from typing import List, Optional
from fastapi import Body, File, UploadFile, Query
import sqlite3
from ..utils.system_utils import BaseResponse, ListResponse


def create_agent(
        agent_name: str = Body(..., examples=["ChatGPT Agent"]),
        agent_abstract: str = Body("", description="Agent简介。"),
        agent_info: str = Body("", description="Agent详细配置信息"),
        temperature: float = Body(0.8, description="LLM温度"),
        max_tokens: int = Body(4096, description="模型输出最大长度"),
        tool_config: List[str] = Body([], description="工具配置", examples=[["search_internet", "weather_check"]]),
        # kb_files: Optional[List[UploadFile]] = File(None, description="知识库文件"),
        kb_files: List[UploadFile] = File(None, description="知识库文件"),
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
        tool_config TEXT,
        kb_files TEXT
    )
    ''')
    conn.commit()

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")

    cursor.execute('SELECT id FROM agents WHERE agent_name = ?', (agent_name,))
    existing_agent = cursor.fetchone()
    if existing_agent:
        return BaseResponse(code=404, msg=f"已存在同名Agent {agent_name}")

    # TODO 处理上传的知识库文件
    kb_files_list = []
    if kb_files:
        for file in kb_files:
            kb_files_list.append(file.filename)

    cursor.execute('''
        INSERT INTO agents (agent_name, agent_abstract, agent_info, temperature, max_tokens, tool_config, kb_files)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
    agent_name, agent_abstract, agent_info, temperature, max_tokens, ','.join(tool_config), ','.join(kb_files_list)))
    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg=f"已新增Agent {agent_name}")


def delete_agent(
        agent_name: str = Body(..., examples=["ChatGPT Agent"])
) -> BaseResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")

    cursor.execute('SELECT id FROM agents WHERE agent_name = ?', (agent_name,))
    existing_agent = cursor.fetchone()
    if not existing_agent:
        return BaseResponse(code=404, msg=f"不存在名为 {agent_name} 的Agent")

    cursor.execute('DELETE FROM agents WHERE agent_name = ?', (agent_name,))
    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg=f"已删除Agent {agent_name}")


def update_agent(
        agent_name: str = Body(..., examples=["ChatGPT Agent"]),
        agent_abstract: str = Body("", description="Agent简介。"),
        agent_info: str = Body("", description="Agent详细配置信息"),
        temperature: float = Body(0.8, description="LLM温度"),
        max_tokens: int = Body(4096, description="模型输出最大长度"),
        tool_config: List[str] = Body([], description="工具配置", examples=[["search_internet", "weather_check"]]),
        # kb_files: Optional[List[UploadFile]] = File(None, description="知识库文件"),
        kb_files: List[UploadFile] = File(None, description="知识库文件"),
) -> BaseResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")

    cursor.execute('SELECT id FROM agents WHERE agent_name = ?', (agent_name,))
    existing_agent = cursor.fetchone()
    if not existing_agent:
        return BaseResponse(code=404, msg=f"不存在名为 {agent_name} 的Agent")

    # 处理上传的知识库文件
    kb_files_list = []
    if kb_files:
        for file in kb_files:
            kb_files_list.append(file.filename)

    cursor.execute('''
        UPDATE agents
        SET agent_abstract = ?, agent_info = ?, temperature = ?, max_tokens = ?, tool_config = ?, kb_files = ?
        WHERE agent_name = ?
        ''', (
    agent_abstract, agent_info, temperature, max_tokens, ','.join(tool_config), ','.join(kb_files_list), agent_name))
    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg=f"已更新Agent {agent_name}")


def list_agent() -> ListResponse:
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
        tool_config TEXT,
        kb_files TEXT
    )
    ''')
    conn.commit()

    cursor.execute('SELECT * FROM agents')
    agents = cursor.fetchall()
    conn.close()

    if not agents:
        return ListResponse(code=200, msg="当前没有Agent信息",data=[])

    # 将查询结果转换为字典列表
    agent_list = []
    for agent in agents:
        agent_dict = {
            "id": agent[0],
            "agent_name": agent[1],
            "agent_abstract": agent[2],
            "agent_info": agent[3],
            "temperature": agent[4],
            "max_tokens": agent[5],
            "tool_config": agent[6].split(',') if agent[6] else [],
            "kb_files": agent[7].split(',') if agent[7] else []
        }
        agent_list.append(agent_dict)

    return ListResponse(code=200, msg="获取Agent列表信息成功", data=agent_list)


def get_agent(
        agent_name: str = Query(..., examples=["ChatGPT Agent"])
):
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")

    cursor.execute('SELECT * FROM agents WHERE agent_name = ?', (agent_name,))
    agent = cursor.fetchone()
    conn.close()

    if not agent:
        return BaseResponse(code=404, msg=f"不存在名为 {agent_name} 的Agent")

    print(agent)
    # 将查询结果转换为字典
    agent_dict = {
        "id": agent[0],
        "agent_name": agent[1],
        "agent_abstract": agent[2],
        "agent_info": agent[3],
        "temperature": agent[4],
        "max_tokens": agent[5],
        "tool_config": agent[6].split(',') if agent[6] else [],
        "kb_files": agent[7].split(',') if agent[7] else []
    }

    return ListResponse(code=200, msg=f"获取Agent {agent_name} 信息成功", data=[agent_dict])
