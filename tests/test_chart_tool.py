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
