"""Tests for FinancialAnalysisTool."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from ecox.agent.tools.financial import FinancialAnalysisTool


def test_financial_tool_properties():
    """测试财务分析工具属性"""
    tool = FinancialAnalysisTool()
    assert tool.name == "financial_analysis"
    assert "财务" in tool.description or "分析" in tool.description


def test_financial_tool_parameters():
    """测试参数定义"""
    tool = FinancialAnalysisTool()
    params = tool.parameters
    assert params["type"] == "object"
    assert "stock_code" in params["properties"]
    assert "modules" in params["properties"]
    assert "stock_code" in params["required"]


def test_financial_tool_execute():
    """测试执行财务分析"""
    tool = FinancialAnalysisTool()

    # Mock the service
    with patch.object(tool, '_get_analysis_result', new_callable=AsyncMock) as mock_analysis:
        mock_analysis.return_value = {
            "stock_code": "SH601318",
            "stock_name": "中国平安",
            "roe": 15.2,
            "net_margin": 12.5
        }

        result = asyncio.run(tool.execute(stock_code="601318"))
        assert result["stock_code"] == "SH601318"
        assert result["roe"] == 15.2
        mock_analysis.assert_called_once()
