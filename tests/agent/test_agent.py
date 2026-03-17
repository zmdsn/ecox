"""Tests for EcoxA Agent."""
import pytest
from unittest.mock import AsyncMock, patch
from ecox.agent.agent import EcoxA
from ecox.agent.models.message import Message


def test_agent_initialization():
    """测试智能体初始化"""
    agent = EcoxA(model="gpt-4")
    assert agent.model == "gpt-4"
    assert agent.max_history == 10


def test_agent_needs_tools():
    """测试判断是否需要工具"""
    agent = EcoxA()
    messages = [
        Message(role="user", content="分析中国平安601318", session_id="test-1")
    ]

    context = agent.conversation_manager.get_context(messages)
    assert agent._needs_tools(context) is True


def test_build_messages():
    """测试构建消息列表"""
    agent = EcoxA()
    messages = [
        Message(role="user", content="你好", session_id="test-1")
    ]

    api_messages = agent._build_messages(messages)
    assert len(api_messages) == 2  # system + user
    assert api_messages[0]["role"] == "system"
    assert api_messages[1]["role"] == "user"
