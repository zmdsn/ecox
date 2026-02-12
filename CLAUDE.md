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

### 依赖说明

- **akshare** - A股数据源
- **backtrader** - 回测框架
- **apscheduler** - 定时任务
- **psycopg2** - PostgreSQL 驱动
- **fastmcp** - MCP 服务器框架
- **apache-iotdb** - 时序数据库（可选）
- **duckdb** - 分析型数据库（可选）

## 注意事项

1. **反爬限制**：akshare 接口有调用频率限制，各脚本中设置了 `CALL_INTERVAL` 参数（通常0.5-360秒）

2. **交易时段判断**：`get_data.py` 中 `is_a_stock_trading_time()` 函数使用 pandas_market_calendars 判断是否为A股交易日

3. **数据复权**：回测使用前复权数据（`adjust="hfq"` 或 `adjust="qfq"`）

4. **目录结构**：
   - `ecox/` - 旧版本脚本（已废弃，被根目录文件替代）
   - `src/ecox/` - MCP 服务器模块
   - 根目录 - 当前活跃的开发文件

5. **开发环境**：Python 3.13，使用 uv 作为包管理器，清华源镜像配置在 pyproject.toml
