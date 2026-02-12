# Ecox 代码库改进计划

## 问题概览

| 类别 | 高优先级 | 中优先级 | 低优先级 | 总计 |
|-----|---------|---------|---------|------|
| 安全问题 | 3 | 0 | 0 | 3 |
| 代码重复 | 6 | 2 | 0 | 8 |
| 代码组织 | 0 | 3 | 1 | 4 |
| 代码质量 | 0 | 1 | 6 | 7 |

---

## 一、安全问题（高优先级）

### 1.1 硬编码数据库密码

**影响范围：** 6个文件

```
get_data.py:28
ecox/get_data.py:28
src/ecox/get_data.py:17
get_shares.py:20
get_report.py:19
get_daily_data.py:14
```

**当前代码：**
```python
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "zmdsn",
    "password": "zmdsnsdmz",  # 暴露在源码中
    "database": "stock",
    "options": "-c client_encoding=utf8"
}
```

**修复方案：**

1. 添加 `.env` 文件（不提交到 git）
```bash
# .env
PG_HOST=localhost
PG_PORT=5432
PG_USER=zmdsn
PG_PASSWORD=your_secure_password
PG_DATABASE=stock
```

2. 创建 `src/ecox/config.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PG_CONFIG = {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", 5432)),
        "user": os.getenv("PG_USER"),
        "password": os.getenv("PG_PASSWORD"),
        "database": os.getenv("PG_DATABASE", "stock"),
        "options": "-c client_encoding=utf8"
    }

class DevConfig(Config):
    pass

class ProdConfig(Config):
    pass

config = DevConfig()  # 根据环境变量切换
```

3. 更新 `.gitignore`
```
.env
.env.local
*.secret
```

---

## 二、代码重复问题（高优先级）

### 2.1 完全重复的文件

| 文件1 | 文件2 | 操作 |
|-------|-------|------|
| `get_data.py` | `ecox/get_data.py` | 删除 `ecox/get_data.py` |
| `get_shares.py` | `ecox/get_shares.py` | 删除 `ecox/get_shares.py` |
| `get_report.py` | `ecox/get_report.py` | 删除 `ecox/get_report.py` |
| `tests/test_get_data.py` | `ecox/tests/test_get_data.py` | 删除 `ecox/tests/` |

### 2.2 重复的数据库连接函数

**位置：** 6个文件都有 `get_pg_connection()` 或 `get_pg_conn()`

**修复方案：** 创建 `src/ecox/db.py`
```python
import psycopg2
from .config import config

def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(**config.PG_CONFIG)
```

### 2.3 重复的工具函数

**code_format 函数重复：**
- `src/ecox/get_data.py:265-281`
- `ecox/get_report.py:203-221`

**修复方案：** 创建 `src/ecox/utils.py`

---

## 三、建议的项目结构

```
ecox/
├── .env                  # 环境变量（不提交）
├── .env.example          # 环境变量模板
├── .gitignore
├── pyproject.toml
├── README.md
├── CLAUDE.md
│
├── src/
│   └── ecox/
│       ├── __init__.py
│       ├── config.py           # 统一配置管理
│       ├── db.py              # 数据库连接
│       ├── utils.py           # 工具函数
│       │
│       ├── data/              # 数据采集模块
│       │   ├── __init__.py
│       │   ├── realtime.py    # 实时行情（原 get_data.py）
│       │   ├── daily.py       # 日线数据（原 get_daily_data.py）
│       │   ├── shares.py      # 股票信息（原 get_shares.py）
│       │   └── report.py      # 财报数据（原 get_report.py）
│       │
│       ├── mcp/               # MCP 服务器
│       │   ├── __init__.py
│       │   └── server.py      # 原 src/ecox/get_data.py
│       │
│       └── strategies/        # 交易策略
│           ├── __init__.py
│           ├── indicators.py  # 原 strategy.py
│           └── analysis.py    # 原 analysis.py
│
├── scripts/                  # 可执行脚本
│   ├── fetch_realtime.py    # 启动实时采集
│   ├── fetch_daily.py       # 启动日线更新
│   └── backtest.py          # 运行回测（原 main.py）
│
├── tests/
│   ├── __init__.py
│   ├── test_data.py
│   └── test_strategies.py
│
├── data/                     # 数据目录（在 .gitignore 中）
│   └── profit_sheets/
│
└── notebooks/                 # Jupyter 笔记本
    └── help.ipynb
```

---

## 四、实施步骤

### 第一步：安全修复（立即执行）
- [ ] 创建 `.env` 文件和 `.env.example`
- [ ] 创建 `src/ecox/config.py`
- [ ] 更新 `.gitignore`
- [ ] 添加 `python-dotenv` 依赖

### 第二步：清理重复文件
- [ ] 删除 `ecox/get_data.py`
- [ ] 删除 `ecox/get_shares.py`
- [ ] 删除 `ecox/get_report.py`
- [ ] 删除 `ecox/tests/` 目录

### 第三步：重构代码
- [ ] 创建 `src/ecox/db.py`
- [ ] 创建 `src/ecox/utils.py`
- [ ] 重新组织数据采集模块

### 第四步：更新导入
- [ ] 修复所有导入路径
- [ ] 更新测试文件
- [ ] 更新文档

---

## 五、依赖更新

需要添加到 `pyproject.toml`:
```toml
dependencies = [
    "python-dotenv>=1.0.0",  # 环境变量管理
    # ... 现有依赖
]
```

---

## 六、代码质量改进

### 6.1 添加类型注解
```python
from typing import Optional, Dict, Any

def get_stock_data(symbol: str = "000001",
                  start_date: str = "20200101",
                  end_date: str = "20231231") -> pd.DataFrame:
    ...
```

### 6.2 统一日志配置
```python
# src/ecox/logging_config.py
import logging

def setup_logger(name: str, log_file: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # ... 统一配置
    return logger
```

### 6.3 代码格式化
```bash
# 添加开发依赖
uv add --dev black ruff mypy

# 格式化代码
black .
ruff check .
```

---

## 七、优先级总结

| 优先级 | 任务 | 预计工作量 |
|-------|------|-----------|
| P0 | 安全修复（密码环境变量） | 30分钟 |
| P0 | 删除重复文件 | 10分钟 |
| P1 | 创建统一配置模块 | 1小时 |
| P1 | 重构数据库连接 | 30分钟 |
| P2 | 重组项目结构 | 2小时 |
| P2 | 更新导入路径 | 1小时 |
| P3 | 添加类型注解 | 持续进行 |
