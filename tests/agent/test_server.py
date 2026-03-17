"""Tests for FastAPI Server."""
from fastapi.testclient import TestClient
from ecox.agent.server import app


def test_health_check():
    """测试健康检查端点"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_models():
    """测试列出模型端点"""
    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0


def test_chat_completions():
    """测试聊天完成端点"""
    from unittest.mock import AsyncMock, patch

    client = TestClient(app)

    # Mock agent.chat
    with patch('ecox.agent.server.agent.chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "这是测试回复"

        response = client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "user", "content": "你好"}
            ]
        })

        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
