import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.conversation_routes import conversation_router
from app.api.config_routes import config_router


@pytest.fixture
def client(tmp_path):
    original = os.getcwd()
    os.chdir(tmp_path)
    try:
        app = FastAPI()
        app.include_router(conversation_router)
        app.include_router(config_router)
        with TestClient(app) as client:
            yield client
    finally:
        os.chdir(original)


def create_profile(client, model):
    response = client.post("/api/model_configs/add", json={
        "config_name": model, "platform": "LOCAL", "base_url": "", "api_key": "",
        "llm_model": {"model": model, "callbacks": True, "temperature": 0.3, "max_tokens": 512},
    })
    assert response.status_code == 200
    return response.json()["data"]["config_id"]


def test_conversation_and_profile_roundtrip(client):
    config_id = create_profile(client, "Qwen2.5-72B-Instruct")
    profile = client.get(f"/api/model_configs/{config_id}").json()["data"]
    assert profile["llm_model"]["model"] == "Qwen2.5-72B-Instruct"
    conversation = client.post("/api/conversation", json=-1).json()["data"]
    identifier = conversation["conversation_id"]
    assert client.get(f"/api/conversation/{identifier}").json()["data"]["messages"] == []
    assert client.delete(f"/api/conversation/{identifier}").json()["code"] == 200
    assert client.get(f"/api/conversation/{identifier}").json()["code"] == 404


def test_unknown_model_rejected_before_message_is_saved(client):
    config_id = create_profile(client, "unknown-model")
    identifier = client.post("/api/conversation", json=0).json()["data"]["conversation_id"]
    response = client.post(f"/api/conversation/{identifier}/messages/stream", json={
        "config_id": config_id, "text": "测试无效模型",
    })
    assert response.status_code == 422
    assert client.get(f"/api/conversation/{identifier}").json()["data"]["messages"] == []


def test_request_validation(client):
    response = client.post("/api/conversation/absent/messages/stream", json={
        "config_id": 1, "text": "你好", "max_tokens": -1,
    })
    assert response.status_code == 422
