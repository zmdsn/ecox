# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Ecox 是一个 A 股数据采集和量化回测系统，主要功能包括：
- 实时行情采集与存储
- 历史日线数据增量更新
- 股票基础信息维护
- 基于 Backtrader 的策略回测
- 财务数据杜邦分析（MCP 服务器）

## 常用命令

### 运行 Python 脚本
```bash
# 使用 uv 运行（推荐）
uv run <script>.py

# 示例
uv run get_data.py          # 启动实时行情采集
uv run get_daily_data.py     # 更新历史日线数据
uv run get_shares.py         # 维护股票基础信息
uv run main.py               # 运行回测
uv run fetch_reports.py --stock 600809  # 下载单股票财报
uv run fetch_reports.py --batch --limit 100  # 批量下载财报
```

### 测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest ecox/tests/test_get_data.py
```

### 包管理
```bash
# 安装依赖
uv sync

# 添加新依赖
uv add <package>
```

## 代码架构

### 数据采集模块（根目录）

- **get_data.py** - 实时行情采集
  - 使用 APScheduler 在交易时段定时抓取数据
  - 数据存储到 PostgreSQL 的 `a_share_real_time` 表
  - 触发时间：9-11点、13-14点，每8分钟一次

- **get_daily_data.py** - 历史日线数据采集
  - 增量更新 `stock_daily_data` 表
  - 自动初始化数据库表结构
  - 支持首次全量拉取（`initial_full_load()`）和日常增量更新（`main_daily_update()`）

- **get_shares.py** - 股票基础信息维护
  - 维护 `a_share_basic` 表（股票代码、名称、行业、上市日期等）
  - 每日6:00自动同步，每周日8:00数据校验

### 回测模块（根目录）

- **main.py** - 回测入口
  - 使用 Backtrader 框架
  - 默认初始资金100万，佣金0.001%

- **strategy.py** - 交易策略定义
  - DoubleMA_Strategy：双均线交叉
  - MacdCross：MACD交叉
  - BollingerBandsBreakout：布林带突破
  - DonchianChannelBreakout：唐奇安通道突破
  - RsiMeanReversion：RSI均值回归

- **get_one_stock.py** - 单股票数据获取（回测专用）
  - 使用 akshare 获取复权日线数据

- **analysis.py** - 回测结果分析
  - 计算夏普比率、最大回撤、年化收益率

### MCP 服务器模块（src/ecox/）

- **src/ecox/get_data.py** - FastMCP 服务器
  - 提供 HTTP API 服务（端口 8080）
  - 工具函数：
    - `get_dupont_analysis()` - 杜邦分析
    - `get_sql_data()` - SQL 查询
    - `code_format()` - 股票代码格式化

### 财报下载模块

- **fetch_reports.py** - 财报下载命令行工具
  - 支持单股票下载：`uv run fetch_reports.py --stock 600809`
  - 支持批量下载：`uv run fetch_reports.py --batch --limit 100`

- **src/ecox/services/financial_report_service.py** - 财报下载服务
  - `fetch_profit_sheet()` - 下载利润表
  - `fetch_balance_sheet()` - 下载资产负债表
  - `fetch_cash_flow_sheet()` - 下载现金流量表
  - `batch_fetch_all_stocks()` - 批量下载所有股票财报
  - 集成数据验证和告警机制

- **src/ecox/validators/report_validator.py** - 财报验证器
  - `validate_profit_sheet()` - 验证利润表数据
  - `validate_balance_sheet()` - 验证资产负债表数据（含勾稽关系检查）
  - `validate_cash_flow_sheet()` - 验证现金流量表数据

### 数据验证模块（src/ecox/validators/）

- **src/ecox/validators/base.py** - 验证器基类
  - `DataValidator` - 抽象基类，定义验证接口
  - 支持单条和批量验证

- **src/ecox/validators/result.py** - 验证结果数据类
  - `ValidationResult` - 封装验证结果、错误和警告

- **src/ecox/validators/price_validator.py** - 价格验证器
  - 验证价格范围、OHLC 逻辑关系
  - 支持 NaN 和无穷大值检测

- **src/ecox/validators/volume_validator.py** - 成交量验证器
  - 验证成交量和成交额的非负性和合理性
  - 检查成交额与成交量的匹配度

- **src/ecox/validators/composite_validator.py** - 组合验证器
  - 支持多个验证器的组合使用
  - 批量验证数据集合

- **src/ecox/config.py** - 统一配置管理
  - `ValidationConfig` - 验证配置类，支持环境变量覆盖
  - 可配置价格范围、成交量范围、涨跌幅限制等参数
  - 支持严格模式和自动清洗模式

### 数据库配置

PostgreSQL 配置（硬编码在各文件中，需注意修改）：
```python
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "zmdsn",
    "password": "zmdsnsdmz",
    "database": "stock",
    "options": "-c client_encoding=utf8"
}
```

### 核心数据表

- `a_share_real_time` - 实时行情表（stock_code, update_time 联合唯一约束）
- `a_share_basic` - 股票基础信息表
- `stock_basic_info` - 股票基本信息（get_daily_data.py 使用）
- `stock_daily_data` - 历史日线数据表
- `update_log` - 更新日志表
- `stock_profit_sheet` - 利润表数据
- `stock_balance_sheet` - 资产负债表数据
- `stock_cash_flow_sheet` - 现金流量表数据
- `data_alerts` - 数据验证告警记录表

### 依赖说明

- **akshare** - A股数据源
- **backtrader** - 回测框架
- **apscheduler** - 定时任务
- **psycopg2** - PostgreSQL 驱动
- **fastmcp** - MCP 服务器框架
- **apache-iotdb** - 时序数据库（可选）
- **duckdb** - 分析型数据库（可选）

### 数据验证模块使用示例

```python
from ecox.validators.price_validator import PriceValidator
from ecox.validators.volume_validator import VolumeValidator
from ecox.validators.composite_validator import CompositeValidator

# 创建验证器实例
price_validator = PriceValidator()
volume_validator = VolumeValidator()

# 使用组合验证器
composite_validator = CompositeValidator([price_validator, volume_validator])

# 验证单条数据
data = {
    "stock_code": "000001",
    "open_price": 10.5,
    "high_price": 11.0,
    "low_price": 10.2,
    "close_price": 10.8,
    "volume": 1000000,
    "amount": 10800000.0,
}
result = composite_validator.validate(data)
if result.is_valid:
    print("数据验证通过")
else:
    print(f"验证失败: {result.errors}")

# 批量验证
data_list = [data1, data2, data3]
results = composite_validator.validate_batch(data_list)
```

### 配置验证参数

在 `.env` 文件中配置验证参数：

```bash
# 价格范围
VALIDATION_MIN_PRICE=0.01
VALIDATION_MAX_PRICE=10000

# 成交量范围
VALIDATION_MIN_VOLUME=0
VALIDATION_MAX_VOLUME=1000000000000

# 涨跌幅限制
VALIDATION_MAX_CHANGE_PCT=20.0

# 验证模式
VALIDATION_STRICT_MODE=false
VALIDATION_AUTO_CLEAN=true
```

## 注意事项

1. **反爬限制**：akshare 接口有调用频率限制，各脚本中设置了 `CALL_INTERVAL` 参数（通常0.5-360秒）

2. **交易时段判断**：`get_data.py` 中 `is_a_stock_trading_time()` 函数使用 pandas_market_calendars 判断是否为A股交易日

3. **数据复权**：回测使用前复权数据（`adjust="hfq"` 或 `adjust="qfq"`）

4. **目录结构**：
   - `ecox/` - 旧版本脚本（已废弃，被根目录文件替代）
   - `src/ecox/` - MCP 服务器模块
   - 根目录 - 当前活跃的开发文件

5. **开发环境**：Python 3.13，使用 uv 作为包管理器，清华源镜像配置在 pyproject.toml

## Ecox AI Agent 模块

Ecox AI Agent 是一个专业的 A 股投资分析智能体系统，使用 LLM + 工具调用实现智能分析。

### 目录结构
- `src/ecox/agent/` - Agent 模块
  - `models/` - 数据模型（Message, Conversation, Context, Entities）
  - `tools/` - 工具实现（Financial, Market, Data, Backtest）
  - `agent.py` - EcoxA 智能体核心类
  - `conversation.py` - 对话管理器
  - `server.py` - FastAPI 服务器
  - `utils/prompts.py` - 系统提示词

### 常用命令

```bash
# 初始化 Agent 数据库表
uv run python scripts/init_agent_tables.py

# 启动 LiteLLM 代理（端口 4000）
uv run python scripts/start_litellm_proxy.py

# 启动 Agent 服务器（端口 8000）
uv run python scripts/start_agent_server.py --port 8000 --reload

# 运行 Agent 测试
uv run pytest tests/agent/ -v

# 运行集成测试
uv run pytest tests/agent/test_integration.py -v
```

### 核心功能

1. **财务分析工具** - 分析 ROE、毛利率、现金流等财务指标
2. **行情数据工具** - 查询实时股价、涨跌幅、成交量
3. **数据查询工具** - 执行 SQL 查询获取历史数据
4. **策略回测工具** - 对股票进行策略回测评估

### API 端点

- `POST /v1/chat/completions` - OpenAI 兼容的聊天 API
- `GET /health` - 健康检查
- `GET /v1/models` - 模型列表
- `GET /docs` - FastAPI 自动生成的文档

### 使用示例

```python
from ecox.agent import EcoxA
from ecox.agent.models.message import Message

# 初始化智能体
agent = EcoxA(model="gpt-4")

# 对话
messages = [
    Message(role="user", content="分析中国平安601318", session_id="demo-1")
]
response = await agent.chat(messages)
```

### 测试

所有测试位于 `tests/agent/`:
- `test_models.py` - 数据模型测试（8 个测试）
- `test_tools/` - 工具测试（20 个测试）
- `test_conversation.py` - 对话管理测试（3 个测试）
- `test_agent.py` - Agent 测试（3 个测试）
- `test_server.py` - 服务器测试（3 个测试）
- `test_integration.py` - 集成测试（2 个测试）

总计：39 个测试，全部通过

### 文档

- `docs/agent-usage.md` - 详细使用指南
- `docs/plans/2026-03-17-ecox-ai-agent-implementation-plan.md` - 实施计划
