import asyncio
import logging
import multiprocessing as mp
import os
import socket
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

import httpx
import openai
from fastapi import FastAPI
from langchain.tools import BaseTool
from langchain_core.embeddings import Embeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.llms import OpenAI

# from chatchat.configs import (
#     DEFAULT_EMBEDDING_MODEL,
#     DEFAULT_LLM_MODEL,
#     HTTPX_DEFAULT_TIMEOUT,
#     MODEL_PLATFORMS,
#     TEMPERATURE,
#     log_verbose,
# )
# from chatchat.server.pydantic_v2 import BaseModel, Field

logger = logging.getLogger()


def set_httpx_config(
        timeout: float = 300,  # TODO 需要设计一个配置文件，修改为可以设置的timeout
        proxy: Union[str, Dict] = None,
        unused_proxies: List[str] = [],
):
    """
    设置httpx默认timeout。httpx默认timeout是5秒，在请求LLM回答时不够用。
    将本项目相关服务加入无代理列表，避免fastchat的服务器请求错误。(windows下无效)
    """

    import os
    import httpx

    httpx._config.DEFAULT_TIMEOUT_CONFIG.connect = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.read = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.write = timeout

    # 在进程范围内设置系统级代理
    proxies = {}
    if isinstance(proxy, str):
        for n in ["http", "https", "all"]:
            proxies[n + "_proxy"] = proxy
    elif isinstance(proxy, dict):
        for n in ["http", "https", "all"]:
            if p := proxy.get(n):
                proxies[n + "_proxy"] = p
            elif p := proxy.get(n + "_proxy"):
                proxies[n + "_proxy"] = p

    for k, v in proxies.items():
        os.environ[k] = v

    # set host to bypass proxy
    no_proxy = [
        x.strip() for x in os.environ.get("no_proxy", "").split(",") if x.strip()
    ]
    no_proxy += [
        # do not use proxy for locahost
        "http://127.0.0.1",
        "http://localhost",
    ]
    # do not use proxy for user deployed fastchat servers
    for x in unused_proxies:
        host = ":".join(x.split(":")[:2])
        if host not in no_proxy:
            no_proxy.append(host)
    os.environ["NO_PROXY"] = ",".join(no_proxy)

    def _get_proxies():
        return proxies

    import urllib.request

    urllib.request.getproxies = _get_proxies


class MsgType:
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    VIDEO = 4


DEFAULT_LLM_MODEL = None  # TODO 设计配置文件修改此处
TEMPERATURE = 0.8


def get_ChatOpenAI(
        model_name: str = DEFAULT_LLM_MODEL,
        base_url: str = "",
        api_key: str = "",
        temperature: float = TEMPERATURE,
        max_tokens: int = None,
        streaming: bool = True,
        callbacks: List[Callable] = [],
        verbose: bool = True,
        **kwargs: Any,
) -> ChatOpenAI:
    params = dict(
        streaming=streaming,
        verbose=verbose,
        callbacks=callbacks,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
    try:
        params.update(
            openai_api_base=base_url,
            openai_api_key=api_key,
            openai_proxy="",

        )
        model = ChatOpenAI(**params)
    except Exception as e:
        logger.error(
            f"failed to create ChatOpenAI for model: {model_name}.", exc_info=True
        )
        model = None
    return model


def get_tool(name: str = None) -> Union[BaseTool, Dict[str, BaseTool]]:
    import importlib

    from src.mindpilot.app import tools

    importlib.reload(tools)

    from src.mindpilot.app.tools import tools_registry

    if name is None:
        return tools_registry._TOOLS_REGISTRY
    else:
        return tools_registry._TOOLS_REGISTRY.get(name)


async def wrap_done(fn: Awaitable, event: asyncio.Event):
    """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
    try:
        await fn
    except Exception as e:
        logging.exception(e)
        msg = f"Caught exception: {e}"
        logger.error(
            f"{e.__class__.__name__}: {msg}", exc_info=e
        )
    finally:
        # Signal the aiter to stop.
        event.set()


def get_tool_config(name: str = None) -> Dict:
    from src.mindpilot.app.configs import TOOL_CONFIG

    if name is None:
        return TOOL_CONFIG
    else:
        return TOOL_CONFIG.get(name, {})
