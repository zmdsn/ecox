# 统一财务分析模型设计文档

## 概述

构建一个统一的公司财务分析模型，整合三大财务报表数据，提供 6 大分析维度的财务指标计算，同时支持 MCP 工具调用和数据库存储。

## 需求总结

| 项目 | 决定 |
|------|------|
| 分析维度 | 盈利能力、现金流分析、偿债能力、营运能力、成长能力、估值指标 |
| 基础数据 | 三大财务报表（利润表、资产负债表、现金流量表） |
| FCF 类型 | FCFF（企业自由现金流）+ FCFE（股权自由现金流） |
| 提供形式 | MCP 工具（实时计算）+ 数据库存储（批量历史数据） |
| 计算公式 | 简化版 |
| 衍生指标 | 完整指标（含 5/10 年 CAGR） |
| 行业对比 | 暂不实现，后续可扩展 |
| 数据来源 | 优先数据库，缺失时用 akshare 补充 |
| 架构 | 分层模块化 |
| 输出格式 | 结构化 JSON |
| 数值精度 | 统一 4 位小数 |

## 架构设计

### 目录结构

```
src/ecox/
├── models/
│   ├── __init__.py                      # 新增 StockFinancialMetrics 模型
│   └── financial_metrics.py             # 财务指标数据类定义
├── services/
│   ├── financial_analysis_service.py    # 统一分析服务（核心计算逻辑）
│   └── financial_report_service.py      # 现有财报下载服务（保持不变）
├── calculators/
│   ├── __init__.py
│   ├── base.py                          # 计算器基类
│   ├── profitability.py                 # 盈利能力计算器
│   ├── cash_flow.py                     # 现金流分析计算器
│   ├── solvency.py                      # 偿债能力计算器
│   ├── efficiency.py                    # 营运能力计算器
│   ├── growth.py                        # 成长能力计算器
│   └── valuation.py                     # 估值指标计算器
└── get_data.py                          # MCP 工具: get_financial_analysis
```

## 数据模型

### StockFinancialMetrics 表

```python
class StockFinancialMetrics(Base):
    """统一财务指标表"""
    __tablename__ = "stock_financial_metrics"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    report_date = Column(String(20), nullable=False, index=True)
    report_type = Column(String(10))  # 年报/中报/季报

    # === 盈利能力 ===
    roe = Column(Numeric(10, 4))               # 净资产收益率
    roa = Column(Numeric(10, 4))               # 总资产收益率
    roic = Column(Numeric(10, 4))              # 投入资本回报率
    gross_margin = Column(Numeric(10, 4))      # 毛利率
    net_margin = Column(Numeric(10, 4))        # 净利率
    operating_margin = Column(Numeric(10, 4))  # 营业利润率

    # === 现金流分析 ===
    fcff = Column(Numeric(20, 4))              # 企业自由现金流
    fcfe = Column(Numeric(20, 4))              # 股权自由现金流
    capex = Column(Numeric(20, 4))             # 资本支出
    cash_conversion_rate = Column(Numeric(10, 4))  # 现金转换率 (FCFF/净利润)
    ocf_to_sales = Column(Numeric(10, 4))      # 经营现金流/营业收入

    # === 偿债能力 ===
    debt_ratio = Column(Numeric(10, 4))        # 资产负债率
    current_ratio = Column(Numeric(10, 4))     # 流动比率
    quick_ratio = Column(Numeric(10, 4))       # 速动比率
    interest_coverage = Column(Numeric(10, 4)) # 利息保障倍数

    # === 营运能力 ===
    inventory_turnover = Column(Numeric(10, 4))      # 存货周转率
    receivables_turnover = Column(Numeric(10, 4))    # 应收账款周转率
    asset_turnover = Column(Numeric(10, 4))          # 总资产周转率

    # === 成长能力 ===
    revenue_growth_1y = Column(Numeric(10, 4))       # 收入增长率(1年)
    profit_growth_1y = Column(Numeric(10, 4))        # 利润增长率(1年)
    revenue_cagr_5y = Column(Numeric(10, 4))         # 收入5年复合增长率
    profit_cagr_5y = Column(Numeric(10, 4))          # 利润5年复合增长率
    fcff_cagr_5y = Column(Numeric(10, 4))            # FCF 5年复合增长率

    # === 估值指标 ===
    pe_ratio = Column(Numeric(10, 4))         # 市盈率
    pb_ratio = Column(Numeric(10, 4))         # 市净率
    ps_ratio = Column(Numeric(10, 4))         # 市销率
    ev_ebitda = Column(Numeric(10, 4))        # EV/EBITDA
    peg_ratio = Column(Numeric(10, 4))        # PEG

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date"),
    )
```

## 计算器模块

### 基类接口

```python
# src/ecox/calculators/base.py
from abc import ABC, abstractmethod
from typing import Any

class BaseCalculator(ABC):
    """计算器基类"""

    @abstractmethod
    def calculate(self, profit_sheet: dict, balance_sheet: dict,
                  cash_flow_sheet: dict, market_data: dict | None = None) -> dict:
        """
        计算财务指标
        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（估值指标需要）
        Returns:
            计算结果字典，所有数值保留4位小数
        """
        pass
```

### 计算器列表

| 计算器 | 文件 | 主要指标 | 计算公式 |
|--------|------|----------|----------|
| ProfitabilityCalculator | profitability.py | ROE, ROA, ROIC, 毛利率, 净利率, 营业利润率 | 净利润/净资产, 净利润/总资产, etc. |
| CashFlowCalculator | cash_flow.py | FCFF, FCFE, CAPEX, 现金转换率 | OCF-CAPEX, FCFF-利息支出 |
| SolvencyCalculator | solvency.py | 资产负债率, 流动比率, 速动比率, 利息保障倍数 | 负债/资产, 流动资产/流动负债, etc. |
| EfficiencyCalculator | efficiency.py | 存货周转率, 应收账款周转率, 总资产周转率 | 营业成本/存货, 营收/应收, etc. |
| GrowthCalculator | growth.py | 收入/利润增长率, 5年CAGR | (本期-上期)/上期, 复合增长率 |
| ValuationCalculator | valuation.py | PE, PB, PS, EV/EBITDA, PEG | 市值/净利润, 市值/净资产, etc. |

### 自由现金流计算公式

**简化版公式**：

- **FCFF（企业自由现金流）**：
  ```
  FCFF = 经营活动现金流净额 - 资本支出
  资本支出 = 购建固定资产、无形资产和其他长期资产支付的现金
  ```

- **FCFE（股权自由现金流）**：
  ```
  FCFE = FCFF - 利息支出 × (1 - 税率) + 净借款变动
  简化版：FCFE = FCFF - 利息支出（忽略税盾和借款）
  ```

## 服务层设计

```python
# src/ecox/services/financial_analysis_service.py

class FinancialAnalysisService:
    """统一财务分析服务"""

    def __init__(self):
        self.calculators = {
            "profitability": ProfitabilityCalculator(),
            "cash_flow": CashFlowCalculator(),
            "solvency": SolvencyCalculator(),
            "efficiency": EfficiencyCalculator(),
            "growth": GrowthCalculator(),
            "valuation": ValuationCalculator(),
        }

    def get_financial_data(self, stock_code: str, report_date: str | None = None) -> dict:
        """
        获取财务数据（优先数据库，缺失时从 akshare 补充）
        Args:
            stock_code: 股票代码
            report_date: 报告日期
        Returns:
            包含三大报表数据的字典
        """
        pass

    def calculate_metrics(self, stock_code: str, report_date: str | None = None,
                         modules: list[str] | None = None) -> dict:
        """
        计算财务指标
        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，默认最新）
            modules: 计算模块列表（可选，默认全部）
                     可选值: ["profitability", "cash_flow", "solvency",
                             "efficiency", "growth", "valuation"]
        Returns:
            完整的财务指标结果
        """
        pass

    def batch_calculate(self, stock_codes: list[str]) -> list[dict]:
        """
        批量计算并存储到数据库
        Args:
            stock_codes: 股票代码列表
        Returns:
            计算结果列表
        """
        pass

    def save_metrics(self, stock_code: str, metrics: dict) -> bool:
        """
        保存计算结果到数据库
        Args:
            stock_code: 股票代码
            metrics: 计算结果字典
        Returns:
            是否保存成功
        """
        pass
```

## MCP 工具

```python
# src/ecox/get_data.py 新增工具

@mcp.tool
async def get_financial_analysis(
    stock_code: str,
    report_date: str | None = None,
    modules: list[str] | None = None
) -> str:
    """
    统一财务分析工具
    Args:
        stock_code: 股票代码（如 600809 或 SH600809）
        report_date: 报告日期（可选，如 2024-12-31，默认最新）
        modules: 分析模块（可选，如 ["profitability", "cash_flow"]，默认全部）
                 可选值: profitability, cash_flow, solvency, efficiency, growth, valuation
    Returns:
        JSON 格式的财务分析结果
    """
    pass
```

## 输出 JSON 结构

```json
{
  "stock_code": "600809",
  "stock_name": "山西汾酒",
  "report_date": "2024-09-30",
  "report_type": "三季报",

  "profitability": {
    "roe": 0.2856,
    "roa": 0.1823,
    "roic": 0.2412,
    "gross_margin": 0.7521,
    "net_margin": 0.3256,
    "operating_margin": 0.4123
  },

  "cash_flow": {
    "fcff": 4523000000.0000,
    "fcfe": 4180000000.0000,
    "capex": 343000000.0000,
    "cash_conversion_rate": 0.8900,
    "ocf_to_sales": 0.4200
  },

  "solvency": {
    "debt_ratio": 0.3612,
    "current_ratio": 2.3500,
    "quick_ratio": 1.8200,
    "interest_coverage": 125.6000
  },

  "efficiency": {
    "inventory_turnover": 1.2500,
    "receivables_turnover": 8.5600,
    "asset_turnover": 0.5600
  },

  "growth": {
    "revenue_growth_1y": 0.1823,
    "profit_growth_1y": 0.2234,
    "revenue_cagr_5y": 0.2156,
    "profit_cagr_5y": 0.2845,
    "fcff_cagr_5y": 0.1932
  },

  "valuation": {
    "pe_ratio": 25.6000,
    "pb_ratio": 7.3200,
    "ps_ratio": 8.4500,
    "ev_ebitda": 18.2000,
    "peg_ratio": 1.1200
  },

  "source": "database",
  "update_time": "2024-03-16T10:30:00Z"
}
```

## 数据来源优先级

1. **优先 PostgreSQL 数据库**
   - 从 `stock_profit_sheet`、`stock_balance_sheet`、`stock_cash_flow_sheet` 表读取
   - 利用 `extra_data` JSON 字段获取完整原始数据

2. **akshare 实时补充**
   - 数据库无数据时，调用 akshare API 获取
   - 获取后可选择是否存储到数据库

3. **市场数据**
   - 估值指标需要实时股价、市值等数据
   - 从 akshare 获取实时行情

## 错误处理

- 缺少必要字段时，对应指标返回 `null`
- 计算过程出现异常时，记录日志并返回 `null`
- 数据源不可用时，返回明确的错误信息

## 后续扩展

- [ ] 行业对比百分位
- [ ] 10 年 CAGR
- [ ] 杜邦分析图表输出
- [ ] 财务健康评分
