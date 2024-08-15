from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from .chat_routes import chat_router
from .tool_routes import tool_router
from .agent_routes import agent_router
from .config_routes import config_router
from .conversation_routes import conversation_router


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
    app.include_router(tool_router)
    app.include_router(agent_router)
    app.include_router(config_router)
    app.include_router(conversation_router)

    return app
