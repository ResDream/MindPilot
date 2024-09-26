import sqlite3
from typing import List
from fastapi import APIRouter, Body, Query
from ..utils.system_utils import BaseResponse, ListResponse, get_mindpilot_db_connection


# 创建表结构
def create_table():
    conn = get_mindpilot_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS model_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model TEXT NOT NULL,
            callbacks BOOLEAN NOT NULL,
            max_tokens INTEGER NOT NULL,
            temperature REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


async def add_model_config(
        config_name: str = Body(..., description="配置名称", examples=["gpt-4o-mini"]),
        platform: str = Body("", description="模型平台", examples=["OpenAI"]),
        base_url: str = Body("", examples=[""]),
        api_key: str = Body("", examples=[""]),
        llm_model: dict = Body({}, description="LLM 模型配置", examples=[{
            "model": "gpt-4o-mini",
            "callbacks": True,
            "max_tokens": 4096,
            "temperature": 0.8
        }]),

):
    create_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO model_configs (
            config_name, platform, base_url, api_key, model, callbacks, max_tokens, temperature
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        config_name,
        platform,
        base_url,
        api_key,
        llm_model['model'],
        llm_model['callbacks'],
        llm_model['max_tokens'],
        llm_model['temperature']
    ))

    config_id = cursor.lastrowid
    conn.commit()
    conn.close()

    config_dict = {
        'config_id': config_id,
        'config_name': config_name,
        'platform': platform,
        'base_url': base_url,
        'api_key': api_key,
        'model': llm_model['model'],
        'callbacks': llm_model['callbacks'],
        'max_tokens': llm_model['max_tokens'],
        'temperature': llm_model['temperature']
    }
    return BaseResponse(code=200, msg="success", data=config_dict)


async def list_model_configs():
    create_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM model_configs')
    rows = cursor.fetchall()

    configs = []
    for row in rows:
        config = {
            "config_id": str(row['id']),
            "config_name": row['config_name'],
            "platform": row['platform'],
            "base_url": row['base_url'],
            "api_key": row['api_key'],
            "llm_model": {
                "model": row['model'],
                "callbacks": row['callbacks'],
                "max_tokens": row['max_tokens'],
                "temperature": row['temperature']
            }
        }
        configs.append(config)

    conn.close()

    return ListResponse(code=200, msg="success", data=configs)


async def get_model_config(
        config_id,

):
    create_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM model_configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return BaseResponse(code=404, msg="Config not found", data=None)

    config = {
        "config_id": str(row['id']),
        "config_name": row['config_name'],
        "platform": row['platform'],
        "base_url": row['base_url'],
        "api_key": row['api_key'],
        "llm_model": {
            "model": row['model'],
            "callbacks": row['callbacks'],
            "max_tokens": row['max_tokens'],
            "temperature": row['temperature']
        }
    }

    conn.close()

    return BaseResponse(code=200, msg="success", data=config)


async def update_model_config(
        config_id: int,
        config_name: str = Body(..., description="配置名称", examples=["gpt-4o-mini"]),
        platform: str = Body("", description="模型平台", examples=["OpenAI"]),
        base_url: str = Body("", examples=[""]),
        api_key: str = Body("", examples=[""]),
        llm_model: dict = Body({}, description="LLM 模型配置", examples=[{
            "model": "gpt-4o-mini",
            "callbacks": True,
            "max_tokens": 4096,
            "temperature": 0.8
        }]),
):
    create_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM model_configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return BaseResponse(code=404, msg="Config not found", data=None)

    cursor.execute('''
        UPDATE model_configs
        SET config_name = ?, platform = ?, base_url = ?, api_key = ?, model = ?, callbacks = ?, max_tokens = ?, temperature = ?
        WHERE id = ?
    ''', (
        config_name,
        platform,
        base_url,
        api_key,
        llm_model['model'],
        llm_model['callbacks'],
        llm_model['max_tokens'],
        llm_model['temperature'],
        config_id
    ))

    conn.commit()
    conn.close()

    config_dict = {
        'config_id': str(config_id),
        'config_name': config_name,
        'platform': platform,
        'base_url': base_url,
        'api_key': api_key,
        'llm_model': {
            'model': llm_model['model'],
            'callbacks': llm_model['callbacks'],
            'max_tokens': llm_model['max_tokens'],
            'temperature': llm_model['temperature']
        }
    }
    return BaseResponse(code=200, msg="success", data=config_dict)


async def delete_model_config(config_id):
    create_table()
    conn = get_mindpilot_db_connection()
    cursor = conn.cursor()

    # 首先检查配置是否存在
    cursor.execute('SELECT * FROM model_configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return BaseResponse(code=404, msg="Config not found", data=None)

    # 删除配置
    cursor.execute('DELETE FROM model_configs WHERE id = ?', (config_id,))
    conn.commit()
    conn.close()

    response_data = {
        "config_id": str(config_id),
        "message": "Configuration successfully deleted"
    }
    return BaseResponse(code=200, msg="success", data=response_data)
