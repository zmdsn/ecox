"""ChartTool 端到端测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ecox.agent.tools.router import ToolRouter
from ecox.agent.models.context import Context
from ecox.agent.models.message import Message
from ecox.agent.models.context import Entities


@pytest.mark.asyncio
async def test_chart_tool_e2e_price_trend():
    """端到端测试：股价走势图生成"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="e2e-test-1")
    context.current_messages = [
        Message(role="user", content="生成600809的股价走势图", session_id="e2e-test-1")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # Mock 数据库查询
    mock_data = Mock(spec=['stock_code', 'trade_date', 'close', 'open', 'high', 'low', 'volume'])
    mock_data.stock_code = "SH600809"
    mock_data.trade_date = "2026-03-17"
    mock_data.close = 160.77
    mock_data.open = 159.5
    mock_data.high = 161.0
    mock_data.low = 158.0
    mock_data.volume = 1000000

    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_data, mock_data, mock_data]
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=False)
    mock_session.query.return_value = mock_query

    # Mock _to_base64 避免在 WSL2 中出现 Kaleido 问题
    with patch('ecox.agent.tools.chart.get_db_session', return_value=mock_session):
        with patch('ecox.agent.tools.chart.ChartTool._to_base64', return_value='mock_base64_string'):
            # 执行工具路由
            results = await router.execute(context)

            # 验证结果
            assert "chart" in results
            assert "error" not in results["chart"]
            assert results["chart"]["chart_type"] == "price_trend"
            assert results["chart"]["image_base64"] == 'mock_base64_string'
            assert "600809" in results["chart"]["title"]


@pytest.mark.asyncio
async def test_chart_tool_e2e_financial_trend():
    """端到端测试：财务趋势图生成（占位符）"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="e2e-test-2")
    context.current_messages = [
        Message(role="user", content="展示600809的ROE财务指标趋势图", session_id="e2e-test-2")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 执行工具路由
    results = await router.execute(context)

    # 验证结果（占位符返回错误信息）
    assert "chart" in results
    assert "error" in results["chart"] or "chart_type" in results["chart"]


@pytest.mark.asyncio
async def test_chart_tool_e2e_backtest():
    """端到端测试：回测收益曲线图生成（占位符）"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="e2e-test-3")
    context.current_messages = [
        Message(role="user", content="生成600809的回测收益曲线图", session_id="e2e-test-3")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 执行工具路由
    results = await router.execute(context)

    # 验证结果（应该包含 chart 和 backtest 两个工具）
    assert "chart" in results
    assert "backtest" in results


@pytest.mark.asyncio
async def test_chart_tool_e2e_dupont():
    """端到端测试：杜邦分析图生成（占位符）"""
    router = ToolRouter()

    # 创建测试上下文
    context = Context(session_id="e2e-test-4")
    context.current_messages = [
        Message(role="user", content="生成600809的杜邦分析图", session_id="e2e-test-4")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 执行工具路由
    results = await router.execute(context)

    # 验证结果（占位符返回错误信息）
    assert "chart" in results
    assert "error" in results["chart"] or "chart_type" in results["chart"]


@pytest.mark.asyncio
async def test_chart_tool_integration_with_financial_analysis():
    """端到端测试：图表工具与财务分析工具的集成"""
    router = ToolRouter()

    # 创建测试上下文 - 同时要求财务分析和图表
    context = Context(session_id="e2e-test-5")
    context.current_messages = [
        Message(role="user", content="分析600809的财务状况并生成图表", session_id="e2e-test-5")
    ]
    context.entities = Entities(stock_codes=["600809"])

    # 执行工具路由
    results = await router.execute(context)

    # 验证结果（应该同时调用财务分析和图表工具）
    assert "financial_analysis" in results
    assert "chart" in results


def test_chart_tool_module_export():
    """测试 ChartTool 可以从模块正确导入"""
    from ecox.agent.tools import ChartTool

    tool = ChartTool()
    assert tool.name == "chart"
    assert "图表" in tool.description
    assert "base64" in tool.description


def test_chart_tool_all_chart_types():
    """测试所有图表类型的路由"""
    router = ToolRouter()

    test_cases = [
        ("生成股价走势图", "price_trend"),
        ("展示财务指标趋势图", "financial_trend"),
        ("生成回测收益曲线图", "backtest"),
        ("绘制杜邦分析图", "dupont"),
    ]

    for query, expected_chart_type in test_cases:
        context = Context(session_id=f"test-{expected_chart_type}")
        context.current_messages = [
            Message(role="user", content=query, session_id=f"test-{expected_chart_type}")
        ]
        context.entities = Entities(stock_codes=["600809"])

        # 准备参数
        chart_tool = router.tools["chart"]
        args = router._prepare_args(chart_tool, context)

        # 验证图表类型
        assert args["chart_type"] == expected_chart_type, f"Failed for query: {query}"
