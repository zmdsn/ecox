# Plotly 图表工具设计文档

**日期**: 2026-03-17
**状态**: 已批准
**作者**: Claude + 用户协作

---

## 目标

创建一个统一的图表工具，支持生成多种类型的专业金融图表，以 base64 编码格式返回给前端展示。

---

## 背景

### 用户需求
> "能否绘制折线图使用base64返回给前端"

### 支持的图表类型
1. **股价走势图** - 显示股票价格历史走势
2. **财务指标趋势图** - 显示ROE、毛利率等财务指标的历史趋势
3. **回测收益曲线** - 显示策略回测的累计收益率
4. **杜邦分析图示** - 可视化ROE拆解

### 技术选型
- **图表库**: Plotly（用户选定）
- **输出格式**: base64 编码的 PNG 图片
- **工具类型**: 单一多用途工具（用户选定）

---

## 架构设计

### 文件结构
```
src/ecox/agent/tools/
├── chart.py           # 新建：图表工具
├── market.py          # 已有：行情工具（可能调用图表）
├── financial.py       # 已有：财务分析工具（可能调用图表）
└── backtest.py        # 已有：回测工具（可能调用图表）
```

### 工具接口设计

#### 工具元数据
```python
{
    "name": "chart",
    "description": "生成股票相关的专业金融图表（股价走势、财务趋势、回测收益、杜邦分析等）",
    "parameters": {
        "chart_type": "price_trend|financial_trend|backtest|dupont",
        "stock_code": "股票代码（必需）",
        "period": "7d|30d|90d|180d|1y|3y|5y（默认30d）",
        "indicator": "财务指标（用于财务趋势图）",
        "show_ma": "是否显示均线（可选）",
        "backtest_result": "回测结果对象（用于回测收益曲线）"
    }
}
```

#### 返回格式
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

---

## 图表详细设计

### 1. 股价走势图

**类型**: 折线图 + 可选K线图 + 成交量柱状图

**数据源**: `stock_daily_data` 表

**参数**:
- `stock_code` (必需): 股票代码
- `period` (可选): 时间范围，默认 `30d`
- `show_ma` (可选): 是否显示均线，默认 `false`
- `show_volume` (可选): 是否显示成交量，默认 `true`

**实现逻辑**:
```python
def _plot_price_trend(self, stock_code, period="30d", show_ma=False, show_volume=True):
    """绘制股价走势图

    1. 查询 stock_daily_data 表获取历史数据
    2. 根据 period 计算日期范围
    3. 创建 Plotly 图表对象
    4. 添加收盘价折线图
    5. 可选：添加 MA5、MA10、MA20 均线
    6. 可选：底部添加成交量柱状图
    7. 设置图表样式（配色、标题、标签等）
    8. 转换为静态图片 (to_image)
    9. 编码为 base64
    10. 返回结果
    """
```

**样式配置**:
- 主题：金融专业风格（深色/浅色可选）
- 配色：涨跌红绿色彩（A股惯例）
- 布局：响应式布局
- 字体：中文字体支持

---

### 2. 财务指标趋势图

**类型**: 折线图或柱状图

**数据源**: 历史财务报表数据（需要新增时间序列查询）

**参数**:
- `stock_code` (必需): 股票代码
- `indicator` (必需): 财务指标名称
  - 支持的指标：`roe`, `gross_margin`, `net_profit`, `operating_cash_flow`, `revenue`
- `period` (可选): 年份范围，默认 `5y`

**实现逻辑**:
```python
def _plot_financial_trend(self, stock_code, indicator="roe", period="5y"):
    """绘制财务指标趋势图

    1. 从历史财务报表数据中提取指标
    2. 按年份聚合数据
    3. 创建 Plotly 图表
    4. 添加数据标签和趋势线
    5. 设置图表样式
    6. 编码为 base64
    7. 返回结果
    """
```

---

### 3. 回测收益曲线

**类型**: 折线图 + 标注

**数据源**: 回测执行结果

**参数**:
- `backtest_result` (必需): 回测结果字典或对象
- `show_drawdown` (可选): 是否标记最大回撤，默认 `true`

**实现逻辑**:
```python
def _plot_backtest_returns(self, backtest_result, show_drawdown=True):
    """绘制回测收益曲线

    1. 从 backtest_result 提取累计收益率序列
    2. 创建 Plotly 折线图
    3. 可选：标记最大回撤位置
    4. 添加基准线（如沪深300收益率）
    5. 设置图表样式
    6. 编码为 base64
    7. 返回结果
    """
```

---

### 4. 杜邦分析图示

**类型**: 树状图（Treemap）或 瀙斗图（Funnel）

**数据源**: 计算好的杜邦分析数据

**参数**:
- `stock_code` (必需): 股票代码
- `report_date` (可选): 报告日期，默认使用最新

**实现逻辑**:
```python
def _plot_dupont_analysis(self, stock_code, report_date=None):
    """绘制杜邦分析图

    1. 调用财务分析服务计算杜邦分析数据
    2. 提取 ROE 拆解数据：
       - 净资产收益率 = 销售净利率 × 总资产周转率
       - 销售净利率 = 净利润 / 营业收入
       - 总资产周转率 = 营业收入 / 总资产
    3. 创建 Plotly 树状图或瀑布图
    4. 设置标签和数值
    5. 设置图表样式
    6. 编码为 base64
    7. 返回结果
    """
```

---

## 技术实现细节

### Plotly 配置

```python
import plotly.graph_objects as go
import plotly.io as pio
import kaleido
import base64
from io import BytesIO

# 全局配置
pio.kaleido.scope.default_width = 1200
pio.kaleido.scope.default_height = 600
pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_scale = 1  # 高清
```

### Base64 编码

```python
def _to_base64(fig) -> str:
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

### 中文字体支持

```python
# 配置中文字体
font_config = {
    'family': 'SimHei, Arial',  # 使用黑体或 Arial
    'size': 12
}

# 在图表中应用
fig.update_layout(
    font=dict(family='SimHei, Arial')
)
```

### 颜色配置（A股涨跌色）

```python
# A股涨跌色彩
COLOR_UP = '#EF4444'  # 红色（下跌）
COLOR_DOWN = '#10B981'  # 绿色（上涨）

# 应用到价格走势
fig.add_trace(
    go.Scatter(
        ...,
        line=dict(color=COLOR_UP)  # 阳线颜色
    )
)
```

---

## 错误处理策略

### 1. 数据不存在
```python
if not data or data.empty:
    return {
        "error": f"未找到股票 {stock_code} 的{chart_type_desc}数据",
        "stock_code": stock_code,
        "suggestion": "请检查股票代码或尝试其他时间范围"
    }
```

### 2. 数据异常
```python
try:
    fig = create_chart(data)
    img_base64 = _to_base64(fig)
    return {"image_base64": img_base64, ...}
except Exception as e:
    return {
        "error": f"图表生成失败: {str(e)}",
        "chart_type": chart_type,
        "stock_code": stock_code
    }
```

### 3. 参数验证
```python
if chart_type not in ["price_trend", "financial_trend", "backtest", "dupont"]:
    return {
        "error": f"不支持的图表类型: {chart_type}",
        "supported_types": ["price_trend", "financial_trend", "backtest", "dupont"]
    }
```

---

## 集成方案

### 1. 工具路由器更新

在 `router.py` 中添加图表工具：

```python
class ToolRouter:
    def __init__(self):
        self.tools: Dict[str, Any] = {
            "financial_analysis": FinancialAnalysisTool(),
            "market_data": MarketDataTool(),
            "data_query": DataQueryTool(),
            "backtest": BacktestTool(),
            "chart": ChartTool()  # 新增
        }
```

### 2. 智能调用逻辑

在 `_select_tools()` 中添加关键词检测：

```python
# 图表关键词
chart_keywords = ["图表", "走势图", "折线图", "可视化", "绘图", "plot", "chart"]

if any(kw in content for kw in chart_keywords):
    tools.append("chart")
```

### 3. 其他工具调用图表

现有工具可以调用图表工具：

```python
# MarketDataTool 示例
if "图表" in content or "可视化" in content:
    chart_tool = ChartTool()
    chart_result = await chart_tool.execute(
        chart_type="price_trend",
        stock_code=stock_code,
        period="30d"
    )
```

---

## 实施计划

### 阶段 1: 环境准备
1. 安装 Plotly 和 Kaleido：`uv add plotly kaleido`
2. 验证安装：`uv run python -c "import plotly; print(plotly.__version__)"`

### 阶段 2: 核心功能实现
1. 创建 `src/ecox/agent/tools/chart.py`
2. 实现 `ChartTool` 基础结构
3. 实现 `_to_base64()` 辅助方法
4. 实现 `_plot_price_trend()` 方法
5. 实现 `_plot_financial_trend()` 方法
6. 实现 `_plot_backtest_returns()` 方法
7. 实现 `_plot_dupont_analysis()` 方法

### 阶段 3: 样式和美化
1. 设计统一的图表样式模板
2. 配置中文字体支持
3. 配置 A股涨跌色彩
4. 添加图表标题和图例
5. 优化图表布局

### 阶段 4: 集成和测试
1. 更新 `router.py` 添加图表工具
2. 更新 `__init__.py` 导出新工具
3. 编写单元测试
4. 手动测试每种图表类型
5. 验证 base64 编码输出

### 阶段 5: 文档和部署
1. 更新 API 文档
2. 提供使用示例
3. 部署到生产环境

---

## 性能考虑

- 图片生成耗时：约 1-3 秒（取决于数据量）
- 图片大小：约 100-500 KB（PNG 格式）
- 内存占用：图片生成过程中临时占用内存
- 缓存策略：可以添加内存缓存（Redis）避免重复生成

---

## 安全考虑

- 参数验证：严格验证所有输入参数
- 数据查询限制：限制时间范围，避免查询过多数据
- 资源限制：设置最大图表数量限制
- 错误处理：优雅处理所有异常，避免服务崩溃

---

## 审批记录

- **需求提出**: 2026-03-17
- **技术选型**: Plotly (用户选定)
- **设计模式**: 单一多用途工具 (用户选定)
- **支持图表**: 股价走势、财务趋势、回测收益、杜邦分析
- **用户批准**: ✅ 已批准
- **下一步**: 创建实施计划

---

## 相关文档

- 实施计划: `docs/plans/YYYY-MM-DD-chart-tool-implementation.md`
- API 文档: 待更新
- 使用示例: 待添加
