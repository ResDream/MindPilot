from __future__ import annotations
from fastapi import APIRouter, Request
from ..chat.chat import chat

chat_router = APIRouter(prefix="/chat", tags=["MindPilot对话"])

chat_router.post(
    "/online",
    summary="以API方式与在线llm模型进行对话",
)(chat)

