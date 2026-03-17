"""Tests for ConversationManager."""
import pytest
from ecox.agent.conversation import ConversationManager
from ecox.agent.models.message import Message
from ecox.agent.models.context import Context, Entities


def test_conversation_manager_init():
    """测试对话管理器初始化"""
    manager = ConversationManager(max_history=5)
    assert manager.max_history == 5


def test_get_context():
    """测试获取上下文"""
    manager = ConversationManager()
    messages = [
        Message(role="user", content="分析中国平安601318", session_id="test-1")
    ]

    context = manager.get_context(messages)
    assert context.session_id == "test-1"
    assert isinstance(context, Context)


def test_extract_entities():
    """测试提取实体"""
    manager = ConversationManager()
    messages = [
        Message(role="user", content="分析中国平安 601318 在2024-03-15的表现")
    ]

    context = manager.get_context(messages)
    # Check that company name is extracted
    assert "中国平安" in context.entities.company_names
    # Check that dates are extracted
    assert len(context.entities.dates) > 0
