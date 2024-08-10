from __future__ import annotations
from fastapi import APIRouter, Request
from ..agent.agent_api import create_agent

agent_router = APIRouter(prefix="/agent", tags=["Agent配置"])

agent_router.post(
    "/create_agent",
    summary="创建Agent",
)(create_agent)
