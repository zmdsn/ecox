"""Tests for ToolRouter."""
import pytest
import asyncio
from unittest.mock import AsyncMock
from ecox.agent.tools.router import ToolRouter
from ecox.agent.models.context import Context, Entities
from ecox.agent.models.message import Message


def test_router_initialization():
    """测试路由器初始化"""
    router = ToolRouter()
    assert len(router.tools) == 4  # financial, market, data, backtest
    assert "financial_analysis" in router.tools
    assert "market_data" in router.tools


def test_router_select_tools_with_stock_code():
    """测试根据股票代码选择工具"""
    router = ToolRouter()
    entities = Entities(stock_codes=["601318"])
    context = Context(
        session_id="test-1",
        entities=entities,
        current_messages=[Message(role="user", content="分析中国平安", session_id="test-1")]
    )

    tools = router._select_tools(context)
    assert "financial_analysis" in tools
    assert "market_data" in tools


def test_router_execute():
    """测试执行工具"""
    router = ToolRouter()

    # Mock tools
    for tool_name, tool in router.tools.items():
        tool.execute = AsyncMock(return_value={"mock": "result"})

    context = Context(
        session_id="test-1",
        entities=Entities(stock_codes=["601318"]),
        current_messages=[Message(role="user", content="分析中国平安", session_id="test-1")]
    )

    results = asyncio.run(router.execute(context))
    assert "financial_analysis" in results
    assert "market_data" in results
