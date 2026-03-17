"""ChartTool 测试"""
import pytest
from ecox.agent.tools.chart import ChartTool


def test_chart_tool_exists():
    """测试 ChartTool 类存在"""
    tool = ChartTool()
    assert tool is not None
    assert tool.name == "chart"


def test_chart_tool_description():
    """测试工具描述"""
    tool = ChartTool()
    assert "图表" in tool.description
    assert "base64" in tool.description


def test_chart_tool_parameters():
    """测试参数定义"""
    tool = ChartTool()
    params = tool.parameters
    assert params["type"] == "object"
    assert "chart_type" in params["properties"]
    assert "stock_code" in params["properties"]
    assert "chart_type" in params["required"]
    assert "stock_code" in params["required"]
