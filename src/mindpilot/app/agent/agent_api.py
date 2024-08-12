from typing import List, Optional
from fastapi import Body, File, UploadFile, Query
import sqlite3
from ..utils.system_utils import BaseResponse, ListResponse


def create_agent(
        agent_name: str = Body(..., examples=["ChatGPT Agent"]),
        agent_abstract: str = Body("", description="Agent简介"),
        agent_info: str = Body("", description="Agent详细配置信息"),
        temperature: float = Body(0.8, description="LLM温度"),
        max_tokens: int = Body(4096, description="模型输出最大长度"),
        tool_config: List[str] = Body([], description="工具配置", examples=[["search_internet", "weather_check"]]),
        kb_name: List[str] = Body([], examples=[["ChatGPT KB"]]),
        avatar: str = Body("", description="头像图片的Base64编码")
) -> BaseResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL ,
        agent_abstract TEXT,
        agent_info TEXT,
        temperature REAL,
        max_tokens INTEGER,
        tool_config TEXT,
        kb_name TEXT,
        avatar TEXT
    )
    ''')
    conn.commit()

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")

    # TODO 处理知识库

    cursor.execute('''
        INSERT INTO agents (agent_name, agent_abstract, agent_info, temperature, max_tokens, tool_config, kb_name, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        agent_name, agent_abstract, agent_info, temperature, max_tokens, ','.join(tool_config), ','.join(kb_name), avatar))
    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg=f"已新增Agent {agent_name}")


def delete_agent(
        agent_id: int = Body(..., examples=["1"])
) -> BaseResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    if agent_id is None:
        return BaseResponse(code=404, msg="Agent ID不能为空，请重新填写Agent ID")

    cursor.execute('SELECT id FROM agents WHERE id = ?', (agent_id,))
    existing_agent = cursor.fetchone()
    if not existing_agent:
        return BaseResponse(code=404, msg=f"不存在ID为 {agent_id} 的Agent")

    cursor.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg=f"已删除ID为 {agent_id} 的Agent")


def update_agent(
        agent_id: int = Body(..., examples=["1"]),
        agent_name: str = Body(..., examples=["ChatGPT Agent"]),
        agent_abstract: str = Body("", description="Agent简介。"),
        agent_info: str = Body("", description="Agent详细配置信息"),
        temperature: float = Body(0.8, description="LLM温度"),
        max_tokens: int = Body(4096, description="模型输出最大长度"),
        tool_config: List[str] = Body([], description="工具配置", examples=[["search_internet", "weather_check"]]),
        kb_name: List[str] = Body([], examples=[["ChatGPT KB"]]),
        avatar: str = Body("", description="头像图片的Base64编码")
) -> BaseResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    if agent_id is None:
        return BaseResponse(code=404, msg="Agent ID不能为空，请重新填写Agent ID")

    cursor.execute('SELECT id FROM agents WHERE id = ?', (agent_id,))
    existing_agent = cursor.fetchone()
    if not existing_agent:
        return BaseResponse(code=404, msg=f"不存在ID为 {agent_id} 的Agent")

    if agent_name is None or agent_name.strip() == "":
        return BaseResponse(code=404, msg="Agent名称不能为空，请重新填写Agent名称")


    #TODO 处理知识库

    cursor.execute('''
        UPDATE agents
        SET agent_name = ?, agent_abstract = ?, agent_info = ?, temperature = ?, max_tokens = ?, tool_config = ?, kb_name = ?, avatar = ?
        WHERE id = ?
        ''', (
        agent_name, agent_abstract, agent_info, temperature, max_tokens, ','.join(tool_config), ','.join(kb_name), avatar,
        agent_id))
    conn.commit()
    conn.close()

    return BaseResponse(code=200, msg=f"已更新Agent {agent_name}")


def list_agent() -> ListResponse:
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        agent_abstract TEXT,
        agent_info TEXT,
        temperature REAL,
        max_tokens INTEGER,
        tool_config TEXT,
        kb_name TEXT,
        avatar TEXT
    )
    ''')
    conn.commit()

    cursor.execute('SELECT * FROM agents')
    agents = cursor.fetchall()
    conn.close()

    if not agents:
        return ListResponse(code=200, msg="当前没有Agent信息", data=[])

    # 将查询结果转换为字典列表
    agent_list = []
    for agent in agents:
        agent_dict = {
            "agent_id": agent[0],
            "agent_name": agent[1],
            "agent_abstract": agent[2],
            "agent_info": agent[3],
            "temperature": agent[4],
            "max_tokens": agent[5],
            "tool_config": agent[6].split(',') if agent[6] else [],
            "kb_name": agent[7].split(',') if agent[7] else [],
            "avatar": agent[8]
        }
        agent_list.append(agent_dict)

    return ListResponse(code=200, msg="获取Agent列表信息成功", data=agent_list)


def get_agent(
        agent_id: int = Query(..., examples=["1"]),
):
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    if agent_id is None:
        return BaseResponse(code=404, msg="Agent ID不能为空，请重新填写Agent ID")

    cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
    agent = cursor.fetchone()
    conn.close()

    if not agent:
        return BaseResponse(code=404, msg=f"不存在ID为 {agent_id} 的Agent")

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
        "kb_name": agent[7].split(',') if agent[7] else [],
        "avatar": agent[8]
    }

    return ListResponse(code=200, msg=f"获取Agent ID为 {agent_id} 的信息成功", data=[agent_dict])