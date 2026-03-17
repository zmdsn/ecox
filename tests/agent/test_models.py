"""Tests for agent data models."""
import pytest
from datetime import datetime
from ecox.agent.models.message import Message
from ecox.agent.models.conversation import Conversation
from ecox.agent.models.context import Context, Entities


def test_message_creation():
    """测试创建消息对象"""
    msg = Message(
        role="user",
        content="中国平安的ROE是多少？",
        session_id="test-session-123"
    )
    assert msg.role == "user"
    assert msg.content == "中国平安的ROE是多少？"
    assert msg.session_id == "test-session-123"
    assert msg.id is None  # 未保存到数据库


def test_message_with_id():
    """测试带ID的消息"""
    msg = Message(
        id=1,
        role="assistant",
        content="根据财报，中国平安的ROE为15.2%",
        conversation_id=100
    )
    assert msg.id == 1
    assert msg.role == "assistant"
    assert msg.conversation_id == 100


def test_message_invalid_role():
    """测试无效的角色"""
    with pytest.raises(ValueError):
        Message(role="invalid", content="test")


def test_conversation_creation():
    """测试创建对话"""
    conv = Conversation(session_id="test-session-123")
    assert conv.session_id == "test-session-123"
    assert conv.id is None


def test_conversation_with_messages():
    """测试对话关联消息"""
    conv = Conversation(
        id=1,
        session_id="test-session-123",
        metadata={"user": "test_user"}
    )
    assert conv.id == 1
    assert conv.metadata["user"] == "test_user"


def test_entities_creation():
    """测试实体提取结果"""
    entities = Entities()
    assert entities.stock_codes == []
    assert entities.dates == []


def test_entities_with_data():
    """测试带数据的实体"""
    entities = Entities(
        stock_codes=["600809", "SH601318"],
        dates=["2024-09-30", "2024年三季度"]
    )
    assert len(entities.stock_codes) == 2
    assert "600809" in entities.stock_codes
    assert "2024-09-30" in entities.dates


def test_context_creation():
    """测试上下文对象"""
    messages = [
        Message(role="user", content="查询中国平安", session_id="test-1")
    ]
    context = Context(
        session_id="test-1",
        history=[],
        entities=Entities(),
        current_messages=messages
    )
    assert context.session_id == "test-1"
    assert len(context.history) == 0
    assert len(context.current_messages) == 1

