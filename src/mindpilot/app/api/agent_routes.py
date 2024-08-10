from __future__ import annotations
from fastapi import APIRouter, Request
from ..agent.agent_api import create_agent, delete_agent, update_agent, get_agent, list_agent

agent_router = APIRouter(prefix="/agent", tags=["Agent配置"])

agent_router.post(
    "/create_agent",
    summary="创建Agent",
)(create_agent)

agent_router.delete(
    "/delete_agent",
    summary="删除Agent",
)(delete_agent)

agent_router.put(
    "/update_agent",
    summary="更新Agent",
)(update_agent)

agent_router.get(
    "/get_agent",
    summary="获取Agent",
)(get_agent)

agent_router.get(
    "/list_agent",
    summary="获取Agent列表",
)(list_agent)

