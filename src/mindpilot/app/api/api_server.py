import argparse
import os
from typing import Literal

import uvicorn
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from .chat_routes import chat_router
# from .openai_routes import openai_router
# from .server_routes import server_router
# from .tool_routes import tool_router
# from chatchat.server.chat.completion import completion


def create_app(run_mode: str = None):
    app = FastAPI(title="MindPilot API Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", summary="swagger 文档", include_in_schema=False)
    async def document():
        return RedirectResponse(url="/docs")

    app.include_router(chat_router)
    # app.include_router(tool_router)
    # app.include_router(openai_router)
    # app.include_router(server_router)

    # # 其它接口
    # app.post(
    #     "/other/completion",
    #     tags=["Other"],
    #     summary="要求llm模型补全(通过LLMChain)",
    # )(completion)

    return app