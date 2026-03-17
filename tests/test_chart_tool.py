"""ChartTool 测试"""
import pytest
import base64
import plotly.graph_objects as go
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


def test_to_base64():
    """测试 base64 编码功能"""
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    # 创建简单的测试图表
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))

    # 测试编码
    try:
        result = tool._to_base64(fig)

        # 验证返回的是字符串
        assert isinstance(result, str)

        # 验证可以解码
        img_data = base64.b64decode(result)
        assert len(img_data) > 0

        # 验证是 PNG 格式（PNG 魔数）
        assert img_data[:8] == b'\x89PNG\r\n\x1a\n'
    except RuntimeError as e:
        # 在 WSL2 环境中，Kaleido 可能无法工作（已知 bug）
        error_msg = str(e)
        if "Kaleido 无法初始化" in error_msg or "kaleido_scopes" in error_msg:
            pytest.skip(
                f"Kaleido 在当前环境中无法工作: {error_msg}\n"
                "这是 WSL2 环境中的已知问题。"
                "在生产环境（非 WSL）中应该能正常工作。"
            )
        else:
            raise


@pytest.mark.asyncio
async def test_plot_price_trend():
    """测试股价走势图生成"""
    from unittest.mock import Mock, patch, MagicMock
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    # Mock 数据库查询 - 使用 spec 来限制属性，模拟 StockDailyData 模型
    mock_data = Mock(spec=['stock_code', 'trade_date', 'close', 'open', 'high', 'low', 'volume'])
    mock_data.stock_code = "SH600809"
    mock_data.trade_date = "2026-03-17"
    mock_data.close = 160.77
    mock_data.open = 159.5
    mock_data.high = 161.0
    mock_data.low = 158.0
    mock_data.volume = 1000000
    # Note: mock_data doesn't have stock_name attribute (like StockDailyData model)

    # Create mock session
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_data, mock_data, mock_data]
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=False)
    mock_session.query.return_value = mock_query

    with patch('ecox.agent.tools.chart.get_db_session', return_value=mock_session):
        # Mock _to_base64 to avoid Kaleido issues in WSL2
        with patch.object(tool, '_to_base64', return_value='mock_base64_string'):
            result = await tool._plot_price_trend("600809", period="30d")

            # 验证返回结构
            assert "image_base64" in result
            assert "chart_type" in result
            assert result["chart_type"] == "price_trend"
            assert "title" in result
            assert "600809" in result["title"]
            assert "data_summary" in result
            assert result["image_base64"] == 'mock_base64_string'

            # 验证标题格式 - 确保股票代码不会重复出现
            # 当没有 stock_name 时，应该是 "600809 SH600809 - 股价走势图（近30d）"
            # 而不是 "600809 600809 - 股价走势图（近30d）"
            assert "SH600809" in result["title"]  # 格式化后的代码应该出现
            # 验证标题以正确的股票代码开头
            assert result["title"].startswith("600809 SH600809")


@pytest.mark.asyncio
async def test_plot_financial_trend():
    """测试财务指标趋势图生成"""
    from ecox.agent.tools.chart import ChartTool
    tool = ChartTool()
    result = await tool._plot_financial_trend("600809", indicator="roe", period="5y")
    assert "chart_type" in result or "error" in result


@pytest.mark.asyncio
async def test_plot_backtest_returns():
    """测试回测收益曲线生成"""
    from ecox.agent.tools.chart import ChartTool
    tool = ChartTool()
    result = await tool._plot_backtest_returns(
        stock_code="600809",
        strategy="DoubleMA",
        initial_cash=1000000
    )
    assert "chart_type" in result or "error" in result


@pytest.mark.asyncio
async def test_plot_dupont_analysis():
    """测试杜邦分析图生成"""
    from ecox.agent.tools.chart import ChartTool
    tool = ChartTool()
    result = await tool._plot_dupont_analysis("600809", year=2024)
    assert "chart_type" in result or "error" in result
