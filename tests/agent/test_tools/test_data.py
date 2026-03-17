"""Tests for DataQueryTool."""
import pytest
from unittest.mock import patch, AsyncMock
from ecox.agent.tools.data import DataQueryTool


def test_data_tool_properties():
    """测试数据查询工具属性"""
    tool = DataQueryTool()
    assert tool.name == "data_query"
    assert "查询" in tool.description or "SQL" in tool.description


def test_data_tool_execute_sql():
    """测试执行SQL查询"""
    import asyncio
    tool = DataQueryTool()

    with patch('ecox.get_data.run_sql') as mock_sql:
        mock_sql.return_value = {
            "data": [
                {"stock_code": "601318", "stock_name": "中国平安", "close_price": 45.68}
            ]
        }

        result = asyncio.run(tool.execute(sql="SELECT * FROM stock_daily_data LIMIT 1"))
        assert len(result["data"]) == 1
        assert result["data"][0]["stock_code"] == "601318"


def test_data_tool_execute_non_select_fails():
    """测试非SELECT查询被拒绝"""
    import asyncio
    tool = DataQueryTool()

    result = asyncio.run(tool.execute(sql="DELETE FROM stock_daily_data"))
    assert "error" in result
    assert "只支持SELECT查询" in result["error"]
