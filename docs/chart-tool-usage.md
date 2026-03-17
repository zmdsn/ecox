# ChartTool 使用指南

## 概述

ChartTool 是 Ecox AI Agent 的专业金融图表生成工具，支持多种股票相关图表的自动生成，返回 base64 编码的 PNG 图片。

## 功能特性

- **股价走势图**: 展示股票历史价格走势
- **财务指标趋势图**: 展示 ROE、毛利率等财务指标的历史变化（待实现）
- **回测收益曲线图**: 展示策略回测的收益表现（待实现）
- **杜邦分析图**: 可视化杜邦分析结果（待实现）

## 快速开始

### 基本用法

```python
from ecox.agent.tools import ChartTool

# 创建工具实例
tool = ChartTool()

# 生成股价走势图
result = await tool.execute(
    chart_type="price_trend",
    stock_code="600809",
    period="30d",
    show_ma=False
)

# 获取 base64 编码的图片
if "image_base64" in result:
    image_base64 = result["image_base64"]
    # 可以保存为文件或直接在网页中显示
```

### 保存图片到文件

```python
import base64

result = await tool.execute(
    chart_type="price_trend",
    stock_code="600809",
    period="30d"
)

if "image_base64" in result:
    # 解码并保存为 PNG 文件
    img_data = base64.b64decode(result["image_base64"])
    with open("stock_chart.png", "wb") as f:
        f.write(img_data)
```

### 在网页中显示

```html
<!-- HTML 示例 -->
<img src="data:image/png;base64,{image_base64}" alt="股票图表" />
```

```python
# Flask 示例
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/chart")
async def show_chart():
    result = await tool.execute(
        chart_type="price_trend",
        stock_code="600809",
        period="30d"
    )
    return render_template_string(
        '<img src="data:image/png;base64={{ img }}" />',
        img=result["image_base64"]
    )
```

## 参数说明

### 通用参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `chart_type` | string | 是 | 图表类型：`price_trend`、`financial_trend`、`backtest`、`dupont` |
| `stock_code` | string | 是 | 股票代码（如：600809） |

### 股价走势图参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `period` | string | "30d" | 时间范围：7d、30d、90d、180d、1y、3y、5y |
| `show_ma` | boolean | False | 是否显示均线（待实现） |
| `show_volume` | boolean | True | 是否显示成交量（待实现） |

### 财务指标趋势图参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `indicator` | string | "roe" | 财务指标名称（如：roe、gross_margin） |
| `period` | string | "5y" | 年份范围 |

### 回测收益曲线图参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stock_code` | string | None | 股票代码（可选） |
| `strategy` | string | "DoubleMA" | 策略名称 |
| `initial_cash` | float | 1000000 | 初始资金 |
| `start_date` | string | None | 开始日期 |
| `end_date` | string | None | 结束日期 |

### 杜邦分析图参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `year` | int | None | 年份（可选，默认最新年份） |

## 返回值格式

### 成功响应

```python
{
    "chart_type": "price_trend",
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",  # base64 编码的 PNG 图片
    "format": "png",
    "width": 1200,
    "height": 600,
    "title": "600809 SH600809 - 股价走势图（近30d）",
    "data_summary": {
        "start_date": "2026-02-15",
        "end_date": "2026-03-17",
        "data_points": 30
    }
}
```

### 错误响应

```python
{
    "error": "未找到股票 600809 的历史数据",
    "stock_code": "600809",
    "suggestion": "请检查股票代码或尝试其他时间范围"
}
```

## 集成到 AI Agent

ChartTool 已集成到 ToolRouter，可以通过自然语言自动调用：

```python
from ecox.agent.tools.router import ToolRouter
from ecox.agent.models.context import Context
from ecox.agent.models.message import Message

router = ToolRouter()

# 创建对话上下文
context = Context(session_id="demo-1")
context.current_messages = [
    Message(role="user", content="生成600809的股价走势图", session_id="demo-1")
]
context.entities = Entities(stock_codes=["600809"])

# 自动路由到 ChartTool
results = await router.execute(context)

# 获取图表结果
if "chart" in results:
    chart_result = results["chart"]
    # 处理图表...
```

### 支持的自然语言模式

- "生成600809的股价走势图"
- "展示贵州茅台的K线图"
- "绘制平安银行的财务指标趋势图"
- "生成回测收益曲线图"
- "可视化杜邦分析结果"

## 测试

### 运行测试

```bash
# 运行所有 ChartTool 测试
uv run pytest tests/test_chart_tool.py -v

# 运行路由器集成测试
uv run pytest tests/test_router_integration.py -v

# 运行端到端测试
uv run pytest tests/test_chart_e2e.py -v
```

### 测试覆盖

- **单元测试**: 测试各个图表生成方法
- **集成测试**: 测试与 ToolRouter 的集成
- **端到端测试**: 测试完整的用户请求流程

## 技术细节

### 图表生成引擎

- **Plotly Graph Objects**: 用于创建交互式图表
- **Kaleido**: 将 Plotly 图表转换为静态图片（PNG）
- **Base64 编码**: 便于在网络传输和网页展示

### 全局配置

```python
# 默认图表尺寸
pio.defaults.default_width = 1200
pio.defaults.default_height = 600
pio.defaults.default_format = "png"
pio.defaults.default_scale = 1  # 高清
```

### WSL 环境注意事项

在 WSL2 环境中，Kaleido 可能无法正常工作。如果遇到 `kaleido_scopes` 错误：

1. 在非 WSL 环境中运行
2. 安装并配置 xvfb
3. 使用原生 Linux 或 macOS 环境

错误提示会明确说明这是 WSL 环境的已知问题。

## 待实现功能

以下功能当前返回占位符，计划在后续版本实现：

1. **财务指标趋势图**: 需要建立历史财务数据时间序列查询功能
2. **回测收益曲线图**: 需要集成回测引擎或查询回测结果表
3. **杜邦分析图**: 需要集成杜邦分析服务并实现可视化逻辑
4. **均线显示**: 在股价走势图中叠加移动平均线
5. **成交量显示**: 在股价走势图下方显示成交量柱状图

## 开发路线图

- [x] Task 1-4: 基础股价走势图（已完成）
- [x] Task 5: 财务指标趋势图占位符
- [x] Task 6: 回测收益曲线占位符
- [x] Task 7: 杜邦分析图占位符
- [x] Task 8: 集成到工具路由器
- [x] Task 9: 更新模块导出
- [x] Task 10: 端到端测试
- [x] Task 11: 文档编写

## 常见问题

### Q: 为什么有些图表类型返回错误？

A: 财务指标趋势图、回测收益曲线图和杜邦分析图当前是占位符实现，会在后续版本中完成。

### Q: 如何自定义图表样式？

A: 当前使用默认的 Plotly 白色主题。如需自定义，可以修改 `_plot_price_trend()` 方法中的 `template` 参数。

### Q: 支持哪些图片格式？

A: 当前仅支持 PNG 格式。如需其他格式（如 SVG、JPEG），可以修改全局配置或传递 `format` 参数。

### Q: 图表尺寸可以调整吗？

A: 可以。默认是 1200x600 像素。您可以在调用时传递 `width` 和 `height` 参数，或修改全局配置。

## 相关文档

- [Ecox AI Agent 使用指南](./agent-usage.md)
- [财务分析服务文档](../README.md)
- [API 文档](../README.md)

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 ChartTool！

## 许可证

MIT License
