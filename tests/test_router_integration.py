"""工具路由器集成测试"""
import pytest
from ecox.agent.tools.router import ToolRouter
from ecox.agent.models.context import Context
from ecox.agent.models.message import Message
from ecox.agent.models.context import Entities


def test_router_has_chart_tool():
    """测试路由器包含图表工具"""
    router = ToolRouter()
    assert "chart" in router.tools
    assert router.tools["chart"] is not None
    assert router.tools["chart"].name == "chart"


def test_chart_tool_selection():
    """测试图表工具选择逻辑"""
    router = ToolRouter()

    # 创建测试上下文 - 图表相关查询
    context = Context(session_id="test-1")
    context.current_messages = [
        Message(role="user", content="生成600809的股价走势图", session_id="test-1")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 选择工具
    tools = router._select_tools(context)

    # 验证选择了图表工具
    assert "chart" in tools


def test_financial_chart_tool_selection():
    """测试财务图表工具选择逻辑"""
    router = ToolRouter()

    # 创建测试上下文 - 财务趋势图
    context = Context(session_id="test-2")
    context.current_messages = [
        Message(role="user", content="展示600809的ROE财务指标趋势图", session_id="test-2")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 选择工具
    tools = router._select_tools(context)

    # 验证选择了图表工具
    assert "chart" in tools


def test_backtest_chart_tool_selection():
    """测试回测图表工具选择逻辑"""
    router = ToolRouter()

    # 创建测试上下文 - 回测收益曲线
    context = Context(session_id="test-3")
    context.current_messages = [
        Message(role="user", content="生成600809的回测收益曲线图", session_id="test-3")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 选择工具
    tools = router._select_tools(context)

    # 验证选择了图表工具和回测工具
    assert "chart" in tools
    assert "backtest" in tools


def test_chart_tool_args_preparation():
    """测试图表工具参数准备"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="test-4")
    context.current_messages = [
        Message(role="user", content="生成600809的股价走势图", session_id="test-4")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 准备参数
    chart_tool = router.tools["chart"]
    args = router._prepare_args(chart_tool, context)

    # 验证参数
    assert "chart_type" in args
    assert "stock_code" in args
    assert args["stock_code"] == "600809"
    assert args["chart_type"] == "price_trend"


def test_financial_chart_args_preparation():
    """测试财务图表参数准备"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="test-5")
    context.current_messages = [
        Message(role="user", content="展示600809的财务指标趋势图", session_id="test-5")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 准备参数
    chart_tool = router.tools["chart"]
    args = router._prepare_args(chart_tool, context)

    # 验证参数
    assert args["chart_type"] == "financial_trend"
    assert args["stock_code"] == "600809"


def test_dupont_chart_args_preparation():
    """测试杜邦分析图参数准备"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="test-6")
    context.current_messages = [
        Message(role="user", content="生成600809的杜邦分析图", session_id="test-6")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 准备参数
    chart_tool = router.tools["chart"]
    args = router._prepare_args(chart_tool, context)

    # 验证参数
    assert args["chart_type"] == "dupont"
    assert args["stock_code"] == "600809"
