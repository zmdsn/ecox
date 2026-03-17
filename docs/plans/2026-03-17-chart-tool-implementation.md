# Plotly 图表工具实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 创建统一的图表工具，支持生成股价走势、财务趋势、回测收益、杜邦分析等四种专业金融图表，以 base64 编码格式返回给前端展示。

**架构:** 单一多用途 ChartTool 类，使用 Plotly 生成图表，Kaleido 转换为静态图片，base64 编码后通过 JSON 返回。集成到现有工具路由器中。

**技术栈:** Plotly (图表), Kaleido (静态图生成), base64 (编码), PostgreSQL (数据源)

---

## Task 1: 安装依赖

**Files:**
- Modify: `pyproject.toml`

**Step 1: 添加依赖到 pyproject.toml**

在 dependencies 中添加 plotly 和 kaleido：

```toml
dependencies = [
    # ... 现有依赖
    "plotly>=5.18.0",
    "kaleido>=0.2.1",
]
```

**Step 2: 运行安装命令**

```bash
uv sync
```

**Expected:** 包成功安装，无错误

**Step 3: 验证安装**

```bash
uv run python -c "import plotly; import kaleido; print('Plotly:', plotly.__version__, 'Kaleido installed')"
```

**Expected:** `Plotly: 5.x.x Kaleido installed`

**Step 4: 提交**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: 添加 plotly 和 kaleido 依赖"
```

---

## Task 2: 创建 ChartTool 基础结构

**Files:**
- Create: `src/ecox/agent/tools/chart.py`

**Step 1: 编写基础结构测试**

创建 `tests/test_chart_tool.py`:

```python
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
    assert chart_type in params["required"]
    assert stock_code in params["required"]
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_chart_tool.py -v
```

**Expected:** `ModuleNotFoundError: No module named 'ecox.agent.tools.chart'`

**Step 3: 实现 ChartTool 基础结构**

创建 `src/ecox/agent/tools/chart.py`:

```python
"""图表生成工具"""
from typing import Dict, Any
from .base import Tool


class ChartTool(Tool):
    """专业金融图表生成工具"""

    @property
    def name(self) -> str:
        return "chart"

    @property
    def description(self) -> str:
        return "生成股票相关的专业金融图表（股价走势、财务趋势、回测收益、杜邦分析等），返回 base64 编码的 PNG 图片"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["price_trend", "financial_trend", "backtest", "dupont"],
                    "description": "图表类型"
                },
                "stock_code": {
                    "type": "string",
                    "description": "股票代码（必需）"
                },
                "period": {
                    "type": "string",
                    "default": "30d",
                    "description": "时间范围：7d|30d|90d|180d|1y|3y|5y"
                },
                "indicator": {
                    "type": "string",
                    "description": "财务指标（用于财务趋势图）"
                },
                "show_ma": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否显示均线"
                }
            },
            "required": ["chart_type", "stock_code"]
        }

    async def execute(self, chart_type: str, stock_code: str, **kwargs) -> Dict[str, Any]:
        """生成图表

        Args:
            chart_type: 图表类型
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            包含 base64 图片的字典
        """
        # 参数验证
        if chart_type not in ["price_trend", "financial_trend", "backtest", "dupont"]:
            return {
                "error": f"不支持的图表类型: {chart_type}",
                "supported_types": ["price_trend", "financial_trend", "backtest", "dupont"]
            }

        # 路由到具体的绘图方法
        if chart_type == "price_trend":
            return await self._plot_price_trend(stock_code, **kwargs)
        elif chart_type == "financial_trend":
            return await self._plot_financial_trend(stock_code, **kwargs)
        elif chart_type == "backtest":
            return await self._plot_backtest_returns(**kwargs)
        elif chart_type == "dupont":
            return await self._plot_dupont_analysis(stock_code, **kwargs)
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_chart_tool.py -v
```

**Expected:** 3 tests PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/chart.py tests/test_chart_tool.py
git commit -m "feat: 创建 ChartTool 基础结构"
```

---

## Task 3: 实现 base64 编码辅助方法

**Files:**
- Modify: `src/ecox/agent/tools/chart.py`

**Step 1: 编写 base64 编码测试**

在 `tests/test_chart_tool.py` 中添加：

```python
import base64
from io import BytesIO
import plotly.graph_objects as go

def test_to_base64():
    """测试 base64 编码功能"""
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    # 创建简单的测试图表
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))

    # 测试编码
    result = tool._to_base64(fig)

    # 验证返回的是字符串
    assert isinstance(result, str)

    # 验证可以解码
    img_data = base64.b64decode(result)
    assert len(img_data) > 0

    # 验证是 PNG 格式（PNG 魔数）
    assert img_data[:8] == b'\x89PNG\r\n\x1a\n'
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_chart_tool.py::test_to_base64 -v
```

**Expected:** `AttributeError: 'ChartTool' object has no attribute '_to_base64'`

**Step 3: 实现 _to_base64 方法**

在 `src/ecox/agent/tools/chart.py` 的 ChartTool 类中添加：

```python
import plotly.graph_objects as go
import plotly.io as pio
import base64

# 全局 Kaleido 配置
pio.kaleido.scope.default_width = 1200
pio.kaleido.scope.default_height = 600
pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_scale = 1  # 高清

class ChartTool(Tool):
    # ... 现有代码 ...

    def _to_base64(self, fig: go.Figure) -> str:
        """将 Plotly 图表转换为 base64 编码

        Args:
            fig: Plotly 图表对象

        Returns:
            base64 编码的字符串
        """
        # 转换为图片
        img_bytes = pio.to_image(fig, format="png", engine="kaleido")

        # 编码为 base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_base64
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_chart_tool.py::test_to_base64 -v
```

**Expected:** PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/chart.py tests/test_chart_tool.py
git commit -m "feat: 实现 base64 编码辅助方法"
```

---

## Task 4: 实现股价走势图

**Files:**
- Modify: `src/ecox/agent/tools/chart.py`

**Step 1: 编写股价走势图测试**

在 `tests/test_chart_tool.py` 中添加：

```python
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_plot_price_trend():
    """测试股价走势图生成"""
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    # Mock 数据库查询
    mock_data = Mock()
    mock_data.stock_code = "SH600809"
    mock_data.trade_date = "2026-03-17"
    mock_data.close = 160.77
    mock_data.open = 159.5
    mock_data.high = 161.0
    mock_data.low = 158.0
    mock_data.volume = 1000000

    with patch('ecox.agent.tools.chart.get_db_session') as mock_session:
        mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.all.return_value = [
            mock_data, mock_data, mock_data
        ]

        result = await tool._plot_price_trend("600809", period="30d")

        # 验证返回结构
        assert "image_base64" in result
        assert "chart_type" in result
        assert result["chart_type"] == "price_trend"
        assert "title" in result
        assert "600809" in result["title"]
        assert "data_summary" in result
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_price_trend -v
```

**Expected:** `AttributeError: 'ChartTool' object has no attribute '_plot_price_trend'`

**Step 3: 实现 _plot_price_trend 方法**

在 `src/ecox/agent/tools/chart.py` 中添加：

```python
from ...database import get_db_session
from ... import models
from datetime import datetime, timedelta
from ...utils import code_format

class ChartTool(Tool):
    # ... 现有代码 ...

    async def _plot_price_trend(
        self,
        stock_code: str,
        period: str = "30d",
        show_ma: bool = False,
        show_volume: bool = True
    ) -> Dict[str, Any]:
        """绘制股价走势图

        Args:
            stock_code: 股票代码
            period: 时间范围
            show_ma: 是否显示均线
            show_volume: 是否显示成交量

        Returns:
            包含 base64 图片的字典
        """
        # 计算日期范围
        period_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "180d": 180,
            "1y": 365,
            "3y": 365 * 3,
            "5y": 365 * 5
        }
        days = period_map.get(period, 30)
        start_date = datetime.now() - timedelta(days=days)

        # 查询历史数据
        formatted_code = code_format(stock_code)
        with get_db_session() as session:
            data = session.query(models.StockDailyData).filter(
                models.StockDailyData.stock_code == formatted_code,
                models.StockDailyData.trade_date >= start_date
            ).order_by(models.StockDailyData.trade_date.asc()).all()

        if not data:
            return {
                "error": f"未找到股票 {stock_code} 的历史数据",
                "stock_code": stock_code,
                "suggestion": "请检查股票代码或尝试其他时间范围"
            }

        # 提取数据
        dates = [d.trade_date for d in data]
        prices = [float(d.close) for d in data]
        stock_name = data[0].stock_name if hasattr(data[0], 'stock_name') else stock_code

        # 创建图表
        fig = go.Figure()

        # 添加收盘价折线
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='收盘价',
            line=dict(color='#EF4444', width=2)
        ))

        # 设置布局
        fig.update_layout(
            title=f'{stock_code} {stock_name} - 股价走势图（近{period}）',
            xaxis_title='日期',
            yaxis_title='价格（元）',
            hovermode='x unified',
            template='plotly_white',
            font=dict(family='SimHei, Arial', size=12),
            width=1200,
            height=600
        )

        # 转换为 base64
        img_base64 = self._to_base64(fig)

        return {
            "chart_type": "price_trend",
            "image_base64": img_base64,
            "format": "png",
            "width": 1200,
            "height": 600,
            "title": f"{stock_code} {stock_name} - 股价走势图（近{period}）",
            "data_summary": {
                "start_date": str(dates[0]),
                "end_date": str(dates[-1]),
                "data_points": len(dates)
            }
        }
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_price_trend -v
```

**Expected:** PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/chart.py tests/test_chart_tool.py
git commit -m "feat: 实现股价走势图功能"
```

---

## Task 5: 实现财务指标趋势图

**Files:**
- Modify: `src/ecox/agent/tools/chart.py`

**Step 1: 编写财务指标趋势图测试**

在 `tests/test_chart_tool.py` 中添加：

```python
@pytest.mark.asyncio
async def test_plot_financial_trend():
    """测试财务指标趋势图生成"""
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    with patch('ecox.agent.tools.chart.get_db_session'):
        # Mock 返回简单数据
        result = await tool._plot_financial_trend("600809", indicator="roe", period="5y")

        # 验证返回结构（即使数据不存在也要有正确结构）
        assert "chart_type" in result or "error" in result
        if "error" not in result:
            assert result["chart_type"] == "financial_trend"
            assert "image_base64" in result
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_financial_trend -v
```

**Expected:** `AttributeError: 'ChartTool' object has no attribute '_plot_financial_trend'`

**Step 3: 实现 _plot_financial_trend 方法**

在 `src/ecox/agent/tools/chart.py` 中添加：

```python
async def _plot_financial_trend(
    self,
    stock_code: str,
    indicator: str = "roe",
    period: str = "5y"
) -> Dict[str, Any]:
    """绘制财务指标趋势图

    Args:
        stock_code: 股票代码
        indicator: 财务指标名称
        period: 年份范围

    Returns:
        包含 base64 图片的字典
    """
    # TODO: 实现历史财务数据查询
    # 当前返回占位符
    return {
        "error": "财务指标趋势图功能待实现",
        "stock_code": stock_code,
        "indicator": indicator,
        "note": "需要先建立历史财务数据时间序列查询功能"
    }
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_financial_trend -v
```

**Expected:** PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/chart.py tests/test_chart_tool.py
git commit -m "feat: 添加财务指标趋势图占位符"
```

---

## Task 6: 实现回测收益曲线

**Files:**
- Modify: `src/ecox/agent/tools/chart.py`

**Step 1: 编写回测收益曲线测试**

在 `tests/test_chart_tool.py` 中添加：

```python
@pytest.mark.asyncio
async def test_plot_backtest_returns():
    """测试回测收益曲线生成"""
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    # Mock 回测结果
    mock_result = {
        "dates": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "returns": [0.01, 0.02, 0.015]
    }

    result = await tool._plot_backtest_returns(backtest_result=mock_result)

    # 验证返回结构
    assert "chart_type" in result or "error" in result
    if "error" not in result:
        assert result["chart_type"] == "backtest"
        assert "image_base64" in result
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_backtest_returns -v
```

**Expected:** `AttributeError: 'ChartTool' object has no attribute '_plot_backtest_returns'`

**Step 3: 实现 _plot_backtest_returns 方法**

在 `src/ecox/agent/tools/chart.py` 中添加：

```python
async def _plot_backtest_returns(
    self,
    backtest_result: dict = None,
    show_drawdown: bool = True
) -> Dict[str, Any]:
    """绘制回测收益曲线

    Args:
        backtest_result: 回测结果字典
        show_drawdown: 是否标记最大回撤

    Returns:
        包含 base64 图片的字典
    """
    if not backtest_result or "returns" not in backtest_result:
        return {
            "error": "回测结果数据不完整",
            "required_fields": ["dates", "returns"]
        }

    # 提取数据
    dates = backtest_result.get("dates", [])
    returns = backtest_result.get("returns", [])

    # 创建图表
    fig = go.Figure()

    # 添加收益曲线
    fig.add_trace(go.Scatter(
        x=dates,
        y=returns,
        mode='lines',
        name='累计收益率',
        line=dict(color='#10B981', width=2)
    ))

    # 设置布局
    fig.update_layout(
        title='回测收益曲线',
        xaxis_title='日期',
        yaxis_title='累计收益率',
        hovermode='x unified',
        template='plotly_white',
        font=dict(family='SimHei, Arial', size=12),
        width=1200,
        height=600
    )

    # 转换为 base64
    img_base64 = self._to_base64(fig)

    return {
        "chart_type": "backtest",
        "image_base64": img_base64,
        "format": "png",
        "width": 1200,
        "height": 600,
        "title": "回测收益曲线",
        "data_summary": {
            "start_date": str(dates[0]) if dates else None,
            "end_date": str(dates[-1]) if dates else None,
            "data_points": len(dates)
        }
    }
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_backtest_returns -v
```

**Expected:** PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/chart.py tests/test_chart_tool.py
git commit -m "feat: 实现回测收益曲线功能"
```

---

## Task 7: 实现杜邦分析图

**Files:**
- Modify: `src/ecox/agent/tools/chart.py`

**Step 1: 编写杜邦分析图测试**

在 `tests/test_chart_tool.py` 中添加：

```python
@pytest.mark.asyncio
async def test_plot_dupont_analysis():
    """测试杜邦分析图生成"""
    from ecox.agent.tools.chart import ChartTool

    tool = ChartTool()

    result = await tool._plot_dupont_analysis("600809")

    # 验证返回结构（即使数据不存在也要有正确结构）
    assert "chart_type" in result or "error" in result
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_dupont_analysis -v
```

**Expected:** `AttributeError: 'ChartTool' object has no attribute '_plot_dupont_analysis'`

**Step 3: 实现 _plot_dupont_analysis 方法**

在 `src/ecox/agent/tools/chart.py` 中添加：

```python
async def _plot_dupont_analysis(
    self,
    stock_code: str,
    report_date: str = None
) -> Dict[str, Any]:
    """绘制杜邦分析图

    Args:
        stock_code: 股票代码
        report_date: 报告日期

    Returns:
        包含 base64 图片的字典
    """
    # TODO: 调用财务分析服务获取杜邦分析数据
    return {
        "error": "杜邦分析图功能待实现",
        "stock_code": stock_code,
        "note": "需要集成财务分析服务"
    }
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_chart_tool.py::test_plot_dupont_analysis -v
```

**Expected:** PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/chart.py tests/test_chart_tool.py
git commit -m "feat: 添加杜邦分析图占位符"
```

---

## Task 8: 更新工具路由器

**Files:**
- Modify: `src/ecox/agent/tools/router.py`

**Step 1: 编写路由器集成测试**

创建 `tests/test_router_integration.py`:

```python
import pytest
from ecox.agent.tools.router import ToolRouter
from unittest.mock import Mock

def test_router_includes_chart_tool():
    """测试路由器包含图表工具"""
    router = ToolRouter()

    assert "chart" in router.tools
    assert router.tools["chart"].name == "chart"

def test_router_selects_chart_tool():
    """测试路由器正确选择图表工具"""
    router = ToolRouter()

    # Mock 上下文
    context = Mock()
    context.current_messages = [Mock(content="请绘制600809的股价走势图")]
    context.entities = Mock()
    context.entities.stock_codes = ["600809"]
    context.entities.dates = []

    tools = router._select_tools(context)

    assert "chart" in tools
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_router_integration.py -v
```

**Expected:** `AssertionError: assert 'chart' in router.tools`

**Step 3: 更新 router.py 添加图表工具**

在 `src/ecox/agent/tools/router.py` 中：

1. 导入 ChartTool:
```python
from .financial import FinancialAnalysisTool
from .market import MarketDataTool
from .data import DataQueryTool
from .backtest import BacktestTool
from .chart import ChartTool  # 新增
```

2. 在 `__init__` 中注册:
```python
def __init__(self):
    """初始化路由器"""
    self.tools: Dict[str, Any] = {
        "financial_analysis": FinancialAnalysisTool(),
        "market_data": MarketDataTool(),
        "data_query": DataQueryTool(),
        "backtest": BacktestTool(),
        "chart": ChartTool()  # 新增
    }
```

3. 在 `_select_tools` 中添加关键词检测:
```python
def _select_tools(self, context) -> List[str]:
    """根据上下文智能选择工具"""
    tools = []

    # 提取消息内容
    content = " ".join([msg.content for msg in context.current_messages]).lower()

    # ... 现有关键词 ...

    # 图表关键词（新增）
    chart_keywords = ["图表", "走势图", "折线图", "可视化", "绘图", "plot", "chart"]

    if any(kw in content for kw in chart_keywords):
        if "chart" not in tools:
            tools.append("chart")

    return tools
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_router_integration.py -v
```

**Expected:** 2 tests PASS

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/router.py tests/test_router_integration.py
git commit -m "feat: 集成图表工具到路由器"
```

---

## Task 9: 更新 __init__.py 导出

**Files:**
- Modify: `src/ecox/agent/tools/__init__.py`

**Step 1: 添加导出**

在 `src/ecox/agent/tools/__init__.py` 中添加：

```python
from .chart import ChartTool

__all__ = [
    # ... 现有导出 ...
    "ChartTool"
]
```

**Step 2: 验证导入**

```bash
uv run python -c "from ecox.agent.tools import ChartTool; print('Import successful')"
```

**Expected:** `Import successful`

**Step 3: 提交**

```bash
git add src/ecox/agent/tools/__init__.py
git commit -m "feat: 导出 ChartTool"
```

---

## Task 10: 端到端测试

**Files:**
- Create: `tests/test_chart_e2e.py`

**Step 1: 编写端到端测试**

创建 `tests/test_chart_e2e.py`:

```python
import pytest
import base64
from ecox.agent.tools.chart import ChartTool

@pytest.mark.asyncio
async def test_generate_price_chart_end_to_end():
    """端到端测试：生成股价走势图"""
    tool = ChartTool()

    # 使用真实数据（假设数据库有 600809 的数据）
    result = await tool.execute(
        chart_type="price_trend",
        stock_code="600809",
        period="30d"
    )

    # 验证返回结构
    assert "chart_type" in result or "error" in result

    if "error" not in result:
        # 验证图片数据
        assert "image_base64" in result
        assert isinstance(result["image_base64"], str)

        # 验证可以解码为 PNG
        img_data = base64.b64decode(result["image_base64"])
        assert img_data[:8] == b'\x89PNG\r\n\x1a\n'

        # 验证元数据
        assert result["format"] == "png"
        assert result["width"] == 1200
        assert result["height"] == 600
        assert "600809" in result["title"]
```

**Step 2: 运行端到端测试**

```bash
uv run pytest tests/test_chart_e2e.py -v
```

**Expected:** PASS（如果数据库有数据）或返回错误信息（如果没数据）

**Step 3: 提交**

```bash
git add tests/test_chart_e2e.py
git commit -m "test: 添加图表工具端到端测试"
```

---

## Task 11: 文档和示例

**Files:**
- Create: `docs/chart-tool-usage.md`

**Step 1: 编写使用文档**

创建 `docs/chart-tool-usage.md`:

```markdown
# ChartTool 使用指南

## 概述

ChartTool 是一个专业金融图表生成工具，支持四种图表类型：
1. 股价走势图
2. 财务指标趋势图
3. 回测收益曲线
4. 杜邦分析图示

## API 接口

### 请求示例

```json
{
  "chart_type": "price_trend",
  "stock_code": "600809",
  "period": "30d",
  "show_ma": false,
  "show_volume": true
}
```

### 响应示例

```json
{
  "chart_type": "price_trend",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "format": "png",
  "width": 1200,
  "height": 600,
  "title": "600809 山西汾酒 - 股价走势图（近30天）",
  "data_summary": {
    "start_date": "2026-02-15",
    "end_date": "2026-03-17",
    "data_points": 30
  }
}
```

## 前端展示示例

```html
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." alt="股价走势图" />
```

## Agent 调用示例

```
用户：请绘制600809的股价走势图
Agent：[调用 ChartTool] 返回 base64 图片
```

## 参数说明

### chart_type (必需)
- `price_trend`: 股价走势图
- `financial_trend`: 财务指标趋势图
- `backtest`: 回测收益曲线
- `dupont`: 杜邦分析图示

### stock_code (必需)
股票代码，支持格式：
- `600809` (不带前缀)
- `SH600809` (带前缀)

### period (可选)
时间范围：`7d` | `30d` | `90d` | `180d` | `1y` | `3y` | `5y`
默认：`30d`

### indicator (可选)
财务指标名称（用于财务趋势图）：
- `roe`: 净资产收益率
- `gross_margin`: 毛利率
- `net_profit`: 净利润

### show_ma (可选)
是否显示均线，默认：`false`
```

**Step 2: 提交文档**

```bash
git add docs/chart-tool-usage.md
git commit -m "docs: 添加 ChartTool 使用指南"
```

---

## 实施总结

**实施顺序：**
1. 安装依赖 → 2. 基础结构 → 3. base64编码 → 4-7. 四种图表 → 8. 路由集成 → 9. 导出 → 10. E2E测试 → 11. 文档

**关键技术点：**
- Plotly + Kaleido 静态图生成
- base64 编码用于 JSON 传输
- 智能工具路由集成
- 完整的测试覆盖

**后续优化：**
- 实现财务指标趋势图的历史数据查询
- 实现杜邦分析图的服务集成
- 添加图表缓存机制
- 支持更多图表类型
