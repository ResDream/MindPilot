from fastapi import APIRouter
from ..utils.system_utils import get_tool

tool_router = APIRouter(prefix="/tools", tags=["获取工具"])


@tool_router.get("/available_tools", summary="获取可用工具")
async def get_available_tools():
    all_tools = get_tool().values()
    tool_names = [tool.name for tool in all_tools]
    return {"tools": tool_names}
