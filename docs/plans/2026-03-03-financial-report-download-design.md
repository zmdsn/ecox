# 三大报表下载服务设计文档

**日期**: 2026-03-03
**状态**: 已批准
**作者**: Claude + 用户协作设计

---

## 1. 概述

### 1.1 背景
当前 Ecox 系统已有股票基础信息、日线数据和财务报表的数据模型，但缺少完整的财报数据下载服务。本设计旨在建立独立的财报下载服务，支持三大报表（利润表、资产负债表、现金流量表）的完整数据采集。

### 1.2 目标
- 下载所有 A 股的三大财报数据
- 存储完整的财报字段（而非仅核心指标）
- 首次全量下载 + 每日增量更新
- 数据验证确保质量
- 独立服务，便于调度和维护

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────┐
│           FinancialReportService                │
│  ┌─────────────────────────────────────────────┐│
│  │  fetch_profit_sheet()   - 利润表            ││
│  │  fetch_balance_sheet()  - 资产负债表         ││
│  │  fetch_cash_flow_sheet() - 现金流量表       ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              ReportValidator                    │
│  （复用 DataValidator 验证财报字段）            │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         数据库存储 (三大报表表)                  │
│  - stock_profit_sheet                          │
│  - stock_balance_sheet                         │
│  - stock_cash_flow_sheet                       │
└─────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
src/ecox/
├── services/
│   ├── financial_report_service.py    # 财报下载服务（新增）
│   └── report_validator.py            # 财报验证器（新增）
├── validators/
│   └── report_validator.py            # 财报专用验证器（新增）
└── models/
    └── __init__.py                    # 扩展三大报表模型
```

---

## 3. 组件设计

### 3.1 FinancialReportService 核心类

```python
class FinancialReportService:
    """财务报表下载服务"""

    def __init__(self):
        self.validator = ReportValidator()
        self.alert_service = AlertService()

    # 单股票单报表下载
    def fetch_profit_sheet(self, stock_code: str) -> List[Dict]
    def fetch_balance_sheet(self, stock_code: str) -> List[Dict]
    def fetch_cash_flow_sheet(self, stock_code: str) -> List[Dict]

    # 单股票全部报表
    def fetch_all_reports(self, stock_code: str) -> Dict[str, List[Dict]]

    # 批量下载
    def batch_fetch_all_stocks(self, stock_codes: List[str]) -> Dict[str, int]

    # 更新策略
    def initial_full_load(self) -> Dict[str, int]
    def daily_incremental_update(self) -> Dict[str, int]
```

### 3.2 akshare 接口映射

| 报表类型 | akshare 函数 | 字段数 |
|---------|--------------|--------|
| 利润表 | `stock_profit_sheet_by_report_em()` | 80+ |
| 资产负债表 | `stock_balance_sheet_by_report_em()` | 100+ |
| 现金流量表 | `stock_cash_flow_sheet_by_report_em()` | 60+ |

---

## 4. 数据流程

```
┌──────────────────────────────────────────────────────────────────┐
│                     财报下载与验证流程                             │
└──────────────────────────────────────────────────────────────────┘

1. 获取股票列表
   从 a_share_basic 表获取所有股票代码
        │
        ▼
2. 下载财报数据 【首次全量】
   ┌─────────────────────────────────┐
   │ akshare.stock_profit_sheet_by_report_em()    │
   │ akshare.stock_balance_sheet_by_report_em()   │
   │ akshare.stock_cash_flow_sheet_by_report_em() │
   └─────────────────────────────────┘
        │
        ▼
3. 数据验证 【新增】
   ┌─────────────────────────────────┐
   │ ReportValidator.validate()      │
   │ - 检查关键字段非负              │
   │ - 检查勾稽关系                  │
   │ - 检查异常值                    │
   └─────────────────────────────────┘
        │
        ├─────────────────────┬─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ 有效数据 │          │ 可修复  │          │ 无效数据 │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ 入库    │          │ 清洗后  │          │ 记录告警│
   │         │          │ 入库    │          │         │
   └─────────┘          └─────────┘          └─────────┘

【每日增量更新】
- 仅下载最新发布的财报（根据 report_date 判断）
- 使用 stock_code + report_date 唯一约束去重
```

---

## 5. 数据库模型扩展

### 5.1 设计原则

由于财报字段众多（200+），采用 **核心字段 + JSON 存储** 的混合方式：

- **核心字段**（独立列）：常用分析指标，便于 SQL 查询
- **完整数据**（JSON 字段）：所有其他字段，保证数据完整性

### 5.2 利润表模型

```python
class StockProfitSheet(Base):
    """利润表 - 扩展版"""
    __tablename__ = "stock_profit_sheet"

    # 主键和基础信息
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20), index=True)  # 如 "20240930"
    report_type = Column(String(10))  # Q1/Q2/Q3/Q4

    # 核心指标（独立列，便于查询分析）
    total_revenue = Column(Numeric(20, 2))      # 营业总收入
    operating_profit = Column(Numeric(20, 2))   # 营业利润
    net_profit = Column(Numeric(20, 2))         # 净利润
    basic_eps = Column(Numeric(10, 4))          # 基本每股收益

    # 完整数据（JSON 存储）
    extra_data = Column(JSON)  # 存储所有其他字段

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_profit_report"),
    )
```

### 5.3 资产负债表模型

```python
class StockBalanceSheet(Base):
    """资产负债表 - 扩展版"""
    __tablename__ = "stock_balance_sheet"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20), index=True)
    report_type = Column(String(10))

    # 核心指标
    total_assets = Column(Numeric(20, 2))       # 总资产
    total_liabilities = Column(Numeric(20, 2))  # 总负债
    owner_equity = Column(Numeric(20, 2))       # 所有者权益

    extra_data = Column(JSON)

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_balance_report"),
    )
```

### 5.4 现金流量表模型

```python
class StockCashFlowSheet(Base):
    """现金流量表 - 扩展版"""
    __tablename__ = "stock_cash_flow_sheet"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20), index=True)
    report_type = Column(String(10))

    # 核心指标
    operating_cash_flow = Column(Numeric(20, 2))  # 经营活动现金流
    investing_cash_flow = Column(Numeric(20, 2))   # 投资活动现金流
    financing_cash_flow = Column(Numeric(20, 2))   # 筹资活动现金流

    extra_data = Column(JSON)

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_cashflow_report"),
    )
```

---

## 6. 验证规则设计

### 6.1 ReportValidator

```python
class ReportValidator:
    """财报数据验证器"""

    def validate_profit_sheet(self, data: Dict) -> ValidationResult
    def validate_balance_sheet(self, data: Dict) -> ValidationResult
    def validate_cash_flow_sheet(self, data: Dict) -> ValidationResult
```

### 6.2 验证规则

| 验证项 | 规则 | 级别 | 处理方式 |
|--------|------|------|----------|
| 字段非负 | 营业收入、净利润、总资产等 >= 0 | ERROR | 拒绝入库 |
| 勾稽关系 | 资产 = 负债 + 所有者权益 | WARNING | 记录告警，仍入库 |
| 异常检测 | 同比增减超过 200% | WARNING | 记录告警，仍入库 |
| 完整性 | 核心字段不能为空 | ERROR | 拒绝入库 |
| NaN 值 | 所有数值字段不能为 NaN | ERROR | 拒绝入库 |

---

## 7. 配置参数

```python
# src/ecox/config.py 新增

class FinancialReportConfig:
    """财报下载配置"""

    # API 调用间隔（秒）
    REQUEST_INTERVAL = 1.0

    # 批量大小
    BATCH_SIZE = 50

    # 异常检测阈值
    YOY_CHANGE_THRESHOLD = 200  # 同比增减超过 200% 告警

    # 是否启用验证
    ENABLE_VALIDATION = True
```

---

## 8. 测试计划

### 8.1 单元测试

```
tests/services/test_financial_report_service.py
├── test_fetch_profit_sheet
├── test_fetch_balance_sheet
├── test_fetch_cash_flow_sheet
├── test_fetch_all_reports
└── test_batch_fetch

tests/validators/test_report_validator.py
├── test_validate_profit_sheet
├── test_validate_balance_sheet
└── test_validate_cash_flow_sheet
```

### 8.2 集成测试

- 端到端下载流程
- 数据库存储验证
- 告警记录验证

---

## 9. 实施步骤

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 扩展数据库模型（添加 JSON 字段、唯一约束） | 1-2 天 |
| 2 | 实现 FinancialReportService | 2-3 天 |
| 3 | 实现 ReportValidator | 1-2 天 |
| 4 | 集成与测试 | 1-2 天 |
| 5 | 首次全量下载 | 视数据量 |

---

## 10. 扩展性考虑

### 10.1 未来可扩展功能

- 支持港股、美股财报
- 财报数据可视化
- 财务指标计算（ROE、ROA 等）
- 财报异常检测（AI 辅助）
- 定时任务调度（季度自动更新）

### 10.2 性能考虑

- 批量下载减少 API 调用
- 异步下载提升效率
- 数据库连接池优化
- JSON 字段索引优化
