import asyncio
import logging
import multiprocessing
import multiprocessing as mp
import os
import sys
from contextlib import asynccontextmanager
from multiprocessing import Process
import argparse
from fastapi import FastAPI
from app.configs import HOST, PORT
from src.mindpilot.app.tools.colorful import print亮蓝

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
    from app.utils import set_httpx_config

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
    print亮蓝(f"OpenAPI 文档：http://{HOST}:{PORT}/docs")

    if sys.version_info < (3, 10):
        loop = asyncio.get_event_loop()
    else:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)
    loop.run_until_complete(start_main_server())


if __name__ == "__main__":
    main()
