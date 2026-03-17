"""Tests for MarketDataTool."""
import pytest
from unittest.mock import patch, MagicMock
from ecox.agent.tools.market import MarketDataTool


def test_market_tool_properties():
    """测试行情工具属性"""
    tool = MarketDataTool()
    assert tool.name == "market_data"
    assert "行情" in tool.description or "股价" in tool.description


def test_market_tool_execute():
    """测试获取行情数据"""
    import asyncio
    tool = MarketDataTool()

    # Mock database query
    mock_result = MagicMock()
    mock_result.stock_code = 'SH601318'
    mock_result.stock_name = '中国平安'
    mock_result.trade_date = '2026-03-17'
    mock_result.open_price = 45.0
    mock_result.high_price = 46.0
    mock_result.low_price = 44.5
    mock_result.close_price = 45.68
    mock_result.volume = 12345678
    mock_result.amount = 567890123.45
    mock_result.change_pct = 2.35

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result

    with patch('ecox.database.get_db_session') as mock_db:
        mock_db.return_value.__enter__.return_value = mock_session

        result = asyncio.run(tool.execute(stock_code="601318"))
        assert result["stock_code"] == "SH601318"
        assert result["close_price"] == 45.68
        assert result["volume"] == 12345678
