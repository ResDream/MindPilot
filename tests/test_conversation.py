import sqlite3
import json
from contextlib import closing

import pytest
from pydantic import ValidationError

from app.conversation.streaming import ConversationStore, MessageRequest, event_message


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "conversations.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(
            "CREATE TABLE conversations (conversation_id TEXT PRIMARY KEY, title TEXT, "
            "updated_at TEXT, is_summarized INTEGER);"
            "CREATE TABLE model_configs (id INTEGER PRIMARY KEY, platform TEXT, base_url TEXT, "
            "api_key TEXT, model TEXT);"
            "CREATE TABLE message (id INTEGER PRIMARY KEY, agent_status INTEGER, role TEXT, "
            "content TEXT, files TEXT, timestamp TEXT, conversation_id TEXT);"
        )
        connection.execute("INSERT INTO conversations VALUES (?, ?, ?, ?)", ("one", "new", "", 0))
        connection.execute("INSERT INTO model_configs VALUES (?, ?, ?, ?, ?)",
                           (1, "LOCAL", "", "", "Qwen2.5-72B-Instruct"))
    return ConversationStore(path)


def test_history_keeps_users_and_final_answers(store):
    store.save("one", 0, "计算十二的平方", role="user")
    store.save("one", 3, json.dumps({"action": "calculate", "action_input": "12*12"}))
    store.save("one", 7, "工具结果")
    store.save("one", -1, "144")
    history, config = store.prepare("one", MessageRequest(config_id=1, text="继续"))
    assert history == [{"role": "user", "content": "计算十二的平方"},
                       {"role": "assistant", "content": "144"}]
    assert next(iter(config["llm_model"])) == "Qwen2.5-72B-Instruct"
    with closing(store.connect()) as connection:
        assert connection.execute("SELECT title FROM conversations").fetchone()[0] == "计算十二的平方"


def test_missing_conversation_does_not_write(store):
    with pytest.raises(LookupError):
        store.prepare("absent", MessageRequest(config_id=1, text="你好"))
    with closing(store.connect()) as connection:
        assert connection.execute("SELECT count(*) FROM message").fetchone()[0] == 0


@pytest.mark.parametrize("changes", [{"max_tokens": 0}, {"temperature": 3}, {"text": ""}])
def test_invalid_request(changes):
    values = {"config_id": 1, "text": "你好", **changes}
    with pytest.raises(ValidationError):
        MessageRequest(**values)


def test_events_keep_only_persistent_messages():
    assert event_message({"type": "token", "text": "a"}) is None
    assert event_message({"type": "answer", "text": "结果"}) == (-1, "结果")
    assert event_message({"type": "tool_end", "text": "144"}) == (7, "Observation:\n144")


def test_legacy_final_answers_remain_in_history(store):
    store.save("one", 3, json.dumps({"action": "Final Answer", "action_input": "144"}))
    store.save("one", 3, "旧本地模型回答")
    history, _ = store.prepare("one", MessageRequest(config_id=1, text="继续"))
    assert [item["content"] for item in history] == ["144", "旧本地模型回答"]
