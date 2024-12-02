import asyncio
import logging
import multiprocessing
import multiprocessing as mp
import os
import sqlite3
import sys
from contextlib import asynccontextmanager
from multiprocessing import Process
import argparse
from fastapi import FastAPI
from app.configs import HOST, PORT
from app.utils.colorful import print亮蓝
from app.configs import KB_INFO
# from src.mindpilot.app.utils.system_utils import get_resource_path
from app.utils.system_utils import get_resource_path

os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"

logger = logging.getLogger()

# 设置numexpr最大线程数，默认为CPU核心数
try:
    import numexpr

    n_cores = numexpr.utils.detect_number_of_cores()
    os.environ["NUMEXPR_MAX_THREADS"] = str(n_cores)
except:
    pass


def _set_app_event(app: FastAPI, started_event: mp.Event = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if started_event is not None:
            started_event.set()
        yield

    app.router.lifespan_context = lifespan


def run_api_server(
        started_event: mp.Event = None, run_mode: str = None
):
    import uvicorn
    from app.api.api_server import create_app
    from app.utils.system_utils import set_httpx_config

    set_httpx_config()
    app = create_app(run_mode=run_mode)
    _set_app_event(app, started_event)

    uvicorn.run(app, host=HOST, port=PORT)


async def start_main_server():
    import signal

    def handler(signalname):
        def f(signal_received, frame):
            raise KeyboardInterrupt(f"{signalname} received")

        return f

    signal.signal(signal.SIGINT, handler("SIGINT"))
    signal.signal(signal.SIGTERM, handler("SIGTERM"))

    mp.set_start_method("spawn")
    manager = mp.Manager()
    run_mode = None

    processes = {}

    def process_count():
        return len(processes)

    api_started = manager.Event()
    process = Process(
        target=run_api_server,
        name=f"API Server",
        kwargs=dict(
            started_event=api_started,
            run_mode=run_mode,
        ),
        daemon=False,
    )
    processes["api"] = process

    if process_count() == 0:
        logger.warning("There is no process to start.")
    else:
        try:
            if p := processes.get("api"):
                p.start()
                p.name = f"{p.name} ({p.pid})"
                api_started.wait()  # 等待api.py启动完成

            # 等待所有进程退出
            while processes:
                for p in processes.values():
                    p.join(2)
                    if not p.is_alive():
                        processes.pop(p.name)
        except Exception as e:
            logger.error(e)
            logger.warning("Caught KeyboardInterrupt! Setting stop event...")
        finally:
            for p in processes.values():
                logger.warning("Sending SIGKILL to %s", p)

                if isinstance(p, dict):
                    for process in p.values():
                        process.kill()
                else:
                    p.kill()

            for p in processes.values():
                logger.info("Process status: %s", p)


def main():
    cwd = os.getcwd()
    sys.path.append(cwd)
    multiprocessing.freeze_support()
    print亮蓝(f"当前工作目录：{cwd}")
    print亮蓝(f"OpenAPI 文档地址：http://{HOST}:{PORT}/docs")

    from app.knowledge_base.migrate import create_tables

    create_tables()

    db_path = get_resource_path('mindpilot.db')
    conn = sqlite3.connect(db_path)
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

    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='knowledge_base'
    """)

    if cursor.fetchone() is None:
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kb_name TEXT NOT NULL,
                    kb_info TEXT
                )
            ''')
        conn.commit()

        cursor.execute('''
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

    default_agents = [
        {"id": 0, "agent_name": "默认agent", "agent_abstract": "", "agent_info": "", "temperature": 0.8,
         "max_tokens": 4096,
         "tool_config": "arxiv,calculate,search_internet,search_local_knowledgebase,weather_check,shell,wolfram",
         "kb_name": "", "avatar": ""},
        {"id": -1, "agent_name": "对话模型", "agent_abstract": "", "agent_info": "", "temperature": 0.8,
         "max_tokens": 4096, "tool_config": "", "kb_name": "", "avatar": ""}
    ]

    for agent in default_agents:
        cursor.execute('SELECT id FROM agents WHERE id = ?', (agent["id"],))
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO agents (id, agent_name, agent_abstract, agent_info, temperature, max_tokens, tool_config, kb_name, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (agent["id"], agent["agent_name"], agent["agent_abstract"], agent["agent_info"], agent["temperature"],
                  agent["max_tokens"], agent["tool_config"], agent["kb_name"], agent["avatar"]))
            conn.commit()

    KB_INFO = {}
    cursor.execute('SELECT kb_name,kb_info FROM knowledge_base')
    for kb_name, kb_info in cursor.fetchall():
        KB_INFO[kb_name] = kb_info

    conn.close()

    if sys.version_info < (3, 10):
        loop = asyncio.get_event_loop()
    else:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)
    loop.run_until_complete(start_main_server())


def check_dependencies():
    required_packages = [
        'langchain',
        'fastapi',
        'uvicorn',
        'pydantic',
        'openai',
        'numpy',
        'pandas'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        print("请使用 pip install 安装这些包")
        sys.exit(1)


if __name__ == '__main__':
    check_dependencies()
    main()
