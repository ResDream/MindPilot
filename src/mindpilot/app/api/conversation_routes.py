from __future__ import annotations
from fastapi import APIRouter, Request
from ..conversation.conversation_api import add_conversation, list_conversations, get_conversation, delete_conversation, send_messages

conversation_router = APIRouter(prefix="/api/conversation", tags=["对话接口"])

conversation_router.post(
    "",
    summary="创建conversation",
)(add_conversation)

conversation_router.get(
    "",
    summary="获取conversation列表",
)(list_conversations)

conversation_router.get(
    "{conversation_id}",
    summary="获取单个对话详情"
)(get_conversation)

conversation_router.delete(
    "{conversation_id}",
    summary="删除对话"
)(delete_conversation)

conversation_router.post(
    "{conversation_id}/messages",
    summary="发送消息"
)(send_messages)
