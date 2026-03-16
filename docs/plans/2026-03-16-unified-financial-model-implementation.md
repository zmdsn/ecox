# 统一财务分析模型实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建统一的公司财务分析模型，提供 6 大分析维度的财务指标计算，支持 MCP 工具和数据库存储。

**Architecture:** 分层模块化架构，包含计算器层（6个独立计算器）、服务层（统一分析服务）、数据层（SQLAlchemy 模型）和 MCP 工具层。

**Tech Stack:** Python 3.13, SQLAlchemy, FastMCP, akshare, PostgreSQL

---

## Task 1: 创建计算器基类和目录结构

**Files:**
- Create: `src/ecox/calculators/__init__.py`
- Create: `src/ecox/calculators/base.py`
- Create: `tests/calculators/__init__.py`
- Create: `tests/calculators/test_base.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_base.py
"""计算器基类测试"""

from ecox.calculators.base import BaseCalculator


class TestBaseCalculator:
    """计算器基类测试"""

    def test_base_calculator_is_abstract(self):
        """测试基类是抽象类"""
        assert BaseCalculator.__abstractmethods__ == frozenset({'calculate'})

    def test_round_to_4_decimals(self):
        """测试4位小数舍入"""
        assert BaseCalculator._round(0.123456) == 0.1235
        assert BaseCalculator._round(100.1) == 100.1000
        assert BaseCalculator._round(None) is None

    def test_safe_float(self):
        """测试安全浮点转换"""
        assert BaseCalculator._safe_float(123) == 123.0
        assert BaseCalculator._safe_float("123.45") == 123.45
        assert BaseCalculator._safe_float(None) is None
        assert BaseCalculator._safe_float("N/A") is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'ecox.calculators'"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/__init__.py
"""财务指标计算器模块"""
from .base import BaseCalculator

__all__ = ["BaseCalculator"]
```

```python
# src/ecox/calculators/base.py
"""计算器基类"""
from abc import ABC, abstractmethod
from typing import Any


class BaseCalculator(ABC):
    """计算器基类"""

    @staticmethod
    def _round(value: float | None) -> float | None:
        """保留4位小数"""
        if value is None:
            return None
        return round(float(value), 4)

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """安全转换为浮点数"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @abstractmethod
    def calculate(
        self,
        profit_sheet: dict,
        balance_sheet: dict,
        cash_flow_sheet: dict,
        market_data: dict | None = None,
    ) -> dict:
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

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_base.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/__init__.py src/ecox/calculators/base.py tests/calculators/__init__.py tests/calculators/test_base.py
git commit -m "feat: 添加计算器基类和目录结构"
```

---

## Task 2: 实现盈利能力计算器

**Files:**
- Create: `src/ecox/calculators/profitability.py`
- Create: `tests/calculators/test_profitability.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_profitability.py
"""盈利能力计算器测试"""
import pytest

from ecox.calculators.profitability import ProfitabilityCalculator


class TestProfitabilityCalculator:
    """盈利能力计算器测试"""

    @pytest.fixture
    def calculator(self):
        return ProfitabilityCalculator()

    @pytest.fixture
    def sample_data(self):
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "operating_profit": 200000,
                "net_profit": 150000,
                "operating_cost": 400000,
            },
            "balance_sheet": {
                "total_assets": 5000000,
                "owner_equity": 3000000,
                "total_liabilities": 2000000,
            },
            "cash_flow_sheet": {},
        }

    def test_calculate_roe(self, calculator, sample_data):
        """测试ROE计算"""
        result = calculator.calculate(**sample_data)
        # ROE = 净利润 / 所有者权益 = 150000 / 3000000 = 0.05
        assert result["roe"] == 0.0500

    def test_calculate_roa(self, calculator, sample_data):
        """测试ROA计算"""
        result = calculator.calculate(**sample_data)
        # ROA = 净利润 / 总资产 = 150000 / 5000000 = 0.03
        assert result["roa"] == 0.0300

    def test_calculate_gross_margin(self, calculator, sample_data):
        """测试毛利率计算"""
        result = calculator.calculate(**sample_data)
        # 毛利率 = (营收 - 营业成本) / 营收 = (1000000 - 400000) / 1000000 = 0.6
        assert result["gross_margin"] == 0.6000

    def test_calculate_net_margin(self, calculator, sample_data):
        """测试净利率计算"""
        result = calculator.calculate(**sample_data)
        # 净利率 = 净利润 / 营收 = 150000 / 1000000 = 0.15
        assert result["net_margin"] == 0.1500

    def test_calculate_operating_margin(self, calculator, sample_data):
        """测试营业利润率计算"""
        result = calculator.calculate(**sample_data)
        # 营业利润率 = 营业利润 / 营收 = 200000 / 1000000 = 0.2
        assert result["operating_margin"] == 0.2000

    def test_calculate_with_missing_data(self, calculator):
        """测试缺失数据处理"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["roe"] is None
        assert result["roa"] is None
        assert result["net_margin"] is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_profitability.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/profitability.py
"""盈利能力计算器"""
from typing import Any

from .base import BaseCalculator


class ProfitabilityCalculator(BaseCalculator):
    """盈利能力计算器"""

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """
        计算盈利能力指标

        指标:
        - roe: 净资产收益率 = 净利润 / 所有者权益
        - roa: 总资产收益率 = 净利润 / 总资产
        - roic: 投入资本回报率 = 净利润 / (所有者权益 + 有息负债)
        - gross_margin: 毛利率 = (营收 - 营业成本) / 营收
        - net_margin: 净利率 = 净利润 / 营收
        - operating_margin: 营业利润率 = 营业利润 / 营收
        """
        result = {}

        # 获取基础数据
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        operating_profit = self._safe_float(profit_sheet.get("operating_profit"))
        operating_cost = self._safe_float(profit_sheet.get("operating_cost"))
        total_assets = self._safe_float(balance_sheet.get("total_assets"))
        owner_equity = self._safe_float(balance_sheet.get("owner_equity"))
        total_liabilities = self._safe_float(balance_sheet.get("total_liabilities"))

        # ROE: 净资产收益率
        if net_profit is not None and owner_equity is not None and owner_equity != 0:
            result["roe"] = self._round(net_profit / owner_equity)
        else:
            result["roe"] = None

        # ROA: 总资产收益率
        if net_profit is not None and total_assets is not None and total_assets != 0:
            result["roa"] = self._round(net_profit / total_assets)
        else:
            result["roa"] = None

        # ROIC: 投入资本回报率（简化版，假设有息负债=总负债）
        invested_capital = (owner_equity or 0) + (total_liabilities or 0)
        if net_profit is not None and invested_capital != 0:
            result["roic"] = self._round(net_profit / invested_capital)
        else:
            result["roic"] = None

        # 毛利率
        if (
            total_revenue is not None
            and operating_cost is not None
            and total_revenue != 0
        ):
            result["gross_margin"] = self._round(
                (total_revenue - operating_cost) / total_revenue
            )
        else:
            result["gross_margin"] = None

        # 净利率
        if net_profit is not None and total_revenue is not None and total_revenue != 0:
            result["net_margin"] = self._round(net_profit / total_revenue)
        else:
            result["net_margin"] = None

        # 营业利润率
        if (
            operating_profit is not None
            and total_revenue is not None
            and total_revenue != 0
        ):
            result["operating_margin"] = self._round(operating_profit / total_revenue)
        else:
            result["operating_margin"] = None

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_profitability.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/profitability.py tests/calculators/test_profitability.py
git commit -m "feat: 添加盈利能力计算器"
```

---

## Task 3: 实现现金流分析计算器

**Files:**
- Create: `src/ecox/calculators/cash_flow.py`
- Create: `tests/calculators/test_cash_flow.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_cash_flow.py
"""现金流分析计算器测试"""
import pytest

from ecox.calculators.cash_flow import CashFlowCalculator


class TestCashFlowCalculator:
    """现金流分析计算器测试"""

    @pytest.fixture
    def calculator(self):
        return CashFlowCalculator()

    @pytest.fixture
    def sample_data(self):
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "net_profit": 150000,
                "interest_expense": 10000,
            },
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 200000,
                "capex": 50000,  # 购建固定资产支付的现金
            },
        }

    def test_calculate_fcff(self, calculator, sample_data):
        """测试FCFF计算"""
        result = calculator.calculate(**sample_data)
        # FCFF = 经营现金流 - 资本支出 = 200000 - 50000 = 150000
        assert result["fcff"] == 150000.0000

    def test_calculate_fcfe(self, calculator, sample_data):
        """测试FCFE计算"""
        result = calculator.calculate(**sample_data)
        # FCFE = FCFF - 利息支出 = 150000 - 10000 = 140000
        assert result["fcfe"] == 140000.0000

    def test_calculate_capex(self, calculator, sample_data):
        """测试资本支出"""
        result = calculator.calculate(**sample_data)
        assert result["capex"] == 50000.0000

    def test_calculate_cash_conversion_rate(self, calculator, sample_data):
        """测试现金转换率"""
        result = calculator.calculate(**sample_data)
        # 现金转换率 = FCFF / 净利润 = 150000 / 150000 = 1.0
        assert result["cash_conversion_rate"] == 1.0000

    def test_calculate_ocf_to_sales(self, calculator, sample_data):
        """测试经营现金流/营业收入"""
        result = calculator.calculate(**sample_data)
        # OCF/营收 = 200000 / 1000000 = 0.2
        assert result["ocf_to_sales"] == 0.2000

    def test_calculate_with_negative_fcff(self, calculator):
        """测试负FCFF情况"""
        data = {
            "profit_sheet": {"total_revenue": 1000000, "net_profit": 150000},
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 30000,
                "capex": 100000,
            },
        }
        result = calculator.calculate(**data)
        # FCFF = 30000 - 100000 = -70000
        assert result["fcff"] == -70000.0000
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_cash_flow.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/cash_flow.py
"""现金流分析计算器"""
from typing import Any

from .base import BaseCalculator


class CashFlowCalculator(BaseCalculator):
    """现金流分析计算器"""

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """
        计算现金流分析指标

        指标:
        - fcff: 企业自由现金流 = 经营现金流 - 资本支出
        - fcfe: 股权自由现金流 = FCFF - 利息支出（简化版）
        - capex: 资本支出
        - cash_conversion_rate: 现金转换率 = FCFF / 净利润
        - ocf_to_sales: 经营现金流 / 营业收入
        """
        result = {}

        # 获取基础数据
        operating_cash_flow = self._safe_float(
            cash_flow_sheet.get("operating_cash_flow")
        )
        capex = self._safe_float(cash_flow_sheet.get("capex"))
        interest_expense = self._safe_float(profit_sheet.get("interest_expense"))
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))

        # CAPEX
        result["capex"] = self._round(capex) if capex is not None else None

        # FCFF: 企业自由现金流
        if operating_cash_flow is not None and capex is not None:
            fcff = operating_cash_flow - capex
            result["fcff"] = self._round(fcff)
        else:
            result["fcff"] = None
            fcff = None

        # FCFE: 股权自由现金流（简化版）
        if result["fcff"] is not None:
            fcfe = result["fcff"]
            if interest_expense is not None:
                fcfe = fcfe - interest_expense
            result["fcfe"] = self._round(fcfe)
        else:
            result["fcfe"] = None

        # 现金转换率
        if fcff is not None and net_profit is not None and net_profit != 0:
            result["cash_conversion_rate"] = self._round(fcff / net_profit)
        else:
            result["cash_conversion_rate"] = None

        # 经营现金流/营业收入
        if (
            operating_cash_flow is not None
            and total_revenue is not None
            and total_revenue != 0
        ):
            result["ocf_to_sales"] = self._round(operating_cash_flow / total_revenue)
        else:
            result["ocf_to_sales"] = None

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_cash_flow.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/cash_flow.py tests/calculators/test_cash_flow.py
git commit -m "feat: 添加现金流分析计算器"
```

---

## Task 4: 实现偿债能力计算器

**Files:**
- Create: `src/ecox/calculators/solvency.py`
- Create: `tests/calculators/test_solvency.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_solvency.py
"""偿债能力计算器测试"""
import pytest

from ecox.calculators.solvency import SolvencyCalculator


class TestSolvencyCalculator:
    """偿债能力计算器测试"""

    @pytest.fixture
    def calculator(self):
        return SolvencyCalculator()

    @pytest.fixture
    def sample_data(self):
        return {
            "profit_sheet": {
                "operating_profit": 200000,
                "interest_expense": 10000,
            },
            "balance_sheet": {
                "total_assets": 5000000,
                "total_liabilities": 2000000,
                "current_assets": 1500000,
                "current_liabilities": 800000,
                "inventory": 300000,
                "owner_equity": 3000000,
            },
            "cash_flow_sheet": {},
        }

    def test_calculate_debt_ratio(self, calculator, sample_data):
        """测试资产负债率"""
        result = calculator.calculate(**sample_data)
        # 资产负债率 = 总负债 / 总资产 = 2000000 / 5000000 = 0.4
        assert result["debt_ratio"] == 0.4000

    def test_calculate_current_ratio(self, calculator, sample_data):
        """测试流动比率"""
        result = calculator.calculate(**sample_data)
        # 流动比率 = 流动资产 / 流动负债 = 1500000 / 800000 = 1.875
        assert result["current_ratio"] == 1.8750

    def test_calculate_quick_ratio(self, calculator, sample_data):
        """测试速动比率"""
        result = calculator.calculate(**sample_data)
        # 速动比率 = (流动资产 - 存货) / 流动负债 = (1500000 - 300000) / 800000 = 1.5
        assert result["quick_ratio"] == 1.5000

    def test_calculate_interest_coverage(self, calculator, sample_data):
        """测试利息保障倍数"""
        result = calculator.calculate(**sample_data)
        # 利息保障倍数 = 营业利润 / 利息支出 = 200000 / 10000 = 20
        assert result["interest_coverage"] == 20.0000
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_solvency.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/solvency.py
"""偿债能力计算器"""
from typing import Any

from .base import BaseCalculator


class SolvencyCalculator(BaseCalculator):
    """偿债能力计算器"""

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """
        计算偿债能力指标

        指标:
        - debt_ratio: 资产负债率 = 总负债 / 总资产
        - current_ratio: 流动比率 = 流动资产 / 流动负债
        - quick_ratio: 速动比率 = (流动资产 - 存货) / 流动负债
        - interest_coverage: 利息保障倍数 = 营业利润 / 利息支出
        """
        result = {}

        # 获取基础数据
        total_assets = self._safe_float(balance_sheet.get("total_assets"))
        total_liabilities = self._safe_float(balance_sheet.get("total_liabilities"))
        current_assets = self._safe_float(balance_sheet.get("current_assets"))
        current_liabilities = self._safe_float(balance_sheet.get("current_liabilities"))
        inventory = self._safe_float(balance_sheet.get("inventory"))
        operating_profit = self._safe_float(profit_sheet.get("operating_profit"))
        interest_expense = self._safe_float(profit_sheet.get("interest_expense"))

        # 资产负债率
        if total_liabilities is not None and total_assets is not None and total_assets != 0:
            result["debt_ratio"] = self._round(total_liabilities / total_assets)
        else:
            result["debt_ratio"] = None

        # 流动比率
        if current_assets is not None and current_liabilities is not None and current_liabilities != 0:
            result["current_ratio"] = self._round(current_assets / current_liabilities)
        else:
            result["current_ratio"] = None

        # 速动比率
        if current_assets is not None and inventory is not None and current_liabilities is not None and current_liabilities != 0:
            result["quick_ratio"] = self._round(
                (current_assets - inventory) / current_liabilities
            )
        else:
            result["quick_ratio"] = None

        # 利息保障倍数
        if operating_profit is not None and interest_expense is not None and interest_expense != 0:
            result["interest_coverage"] = self._round(operating_profit / interest_expense)
        else:
            result["interest_coverage"] = None

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_solvency.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/solvency.py tests/calculators/test_solvency.py
git commit -m "feat: 添加偿债能力计算器"
```

---

## Task 5: 实现营运能力计算器

**Files:**
- Create: `src/ecox/calculators/efficiency.py`
- Create: `tests/calculators/test_efficiency.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_efficiency.py
"""营运能力计算器测试"""
import pytest

from ecox.calculators.efficiency import EfficiencyCalculator


class TestEfficiencyCalculator:
    """营运能力计算器测试"""

    @pytest.fixture
    def calculator(self):
        return EfficiencyCalculator()

    @pytest.fixture
    def sample_data(self):
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "operating_cost": 600000,
            },
            "balance_sheet": {
                "total_assets": 5000000,
                "inventory": 300000,
                "accounts_receivable": 200000,
            },
            "cash_flow_sheet": {},
        }

    def test_calculate_inventory_turnover(self, calculator, sample_data):
        """测试存货周转率"""
        result = calculator.calculate(**sample_data)
        # 存货周转率 = 营业成本 / 存货 = 600000 / 300000 = 2.0
        assert result["inventory_turnover"] == 2.0000

    def test_calculate_receivables_turnover(self, calculator, sample_data):
        """测试应收账款周转率"""
        result = calculator.calculate(**sample_data)
        # 应收账款周转率 = 营收 / 应收账款 = 1000000 / 200000 = 5.0
        assert result["receivables_turnover"] == 5.0000

    def test_calculate_asset_turnover(self, calculator, sample_data):
        """测试总资产周转率"""
        result = calculator.calculate(**sample_data)
        # 总资产周转率 = 营收 / 总资产 = 1000000 / 5000000 = 0.2
        assert result["asset_turnover"] == 0.2000
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_efficiency.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/efficiency.py
"""营运能力计算器"""
from typing import Any

from .base import BaseCalculator


class EfficiencyCalculator(BaseCalculator):
    """营运能力计算器"""

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """
        计算营运能力指标

        指标:
        - inventory_turnover: 存货周转率 = 营业成本 / 存货
        - receivables_turnover: 应收账款周转率 = 营收 / 应收账款
        - asset_turnover: 总资产周转率 = 营收 / 总资产
        """
        result = {}

        # 获取基础数据
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        operating_cost = self._safe_float(profit_sheet.get("operating_cost"))
        total_assets = self._safe_float(balance_sheet.get("total_assets"))
        inventory = self._safe_float(balance_sheet.get("inventory"))
        accounts_receivable = self._safe_float(balance_sheet.get("accounts_receivable"))

        # 存货周转率
        if operating_cost is not None and inventory is not None and inventory != 0:
            result["inventory_turnover"] = self._round(operating_cost / inventory)
        else:
            result["inventory_turnover"] = None

        # 应收账款周转率
        if total_revenue is not None and accounts_receivable is not None and accounts_receivable != 0:
            result["receivables_turnover"] = self._round(
                total_revenue / accounts_receivable
            )
        else:
            result["receivables_turnover"] = None

        # 总资产周转率
        if total_revenue is not None and total_assets is not None and total_assets != 0:
            result["asset_turnover"] = self._round(total_revenue / total_assets)
        else:
            result["asset_turnover"] = None

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_efficiency.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/efficiency.py tests/calculators/test_efficiency.py
git commit -m "feat: 添加营运能力计算器"
```

---

## Task 6: 实现成长能力计算器

**Files:**
- Create: `src/ecox/calculators/growth.py`
- Create: `tests/calculators/test_growth.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_growth.py
"""成长能力计算器测试"""
import pytest

from ecox.calculators.growth import GrowthCalculator


class TestGrowthCalculator:
    """成长能力计算器测试"""

    @pytest.fixture
    def calculator(self):
        return GrowthCalculator()

    @pytest.fixture
    def sample_data(self):
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "net_profit": 150000,
                "prev_total_revenue": 850000,
                "prev_net_profit": 120000,
                "revenue_history": [500000, 600000, 720000, 850000, 1000000],
                "profit_history": [80000, 90000, 105000, 120000, 150000],
                "fcff_history": [60000, 70000, 80000, 90000, 100000],
            },
            "balance_sheet": {},
            "cash_flow_sheet": {},
        }

    def test_calculate_revenue_growth_1y(self, calculator, sample_data):
        """测试收入增长率"""
        result = calculator.calculate(**sample_data)
        # 收入增长 = (1000000 - 850000) / 850000 = 0.1765
        assert result["revenue_growth_1y"] == 0.1765

    def test_calculate_profit_growth_1y(self, calculator, sample_data):
        """测试利润增长率"""
        result = calculator.calculate(**sample_data)
        # 利润增长 = (150000 - 120000) / 120000 = 0.25
        assert result["profit_growth_1y"] == 0.2500

    def test_calculate_revenue_cagr_5y(self, calculator, sample_data):
        """测试收入5年复合增长率"""
        result = calculator.calculate(**sample_data)
        # CAGR = (1000000/500000)^(1/4) - 1 = 0.1895
        assert result["revenue_cagr_5y"] == pytest.approx(0.1895, abs=0.001)

    def test_calculate_profit_cagr_5y(self, calculator, sample_data):
        """测试利润5年复合增长率"""
        result = calculator.calculate(**sample_data)
        # CAGR = (150000/80000)^(1/4) - 1 = 0.1702
        assert result["profit_cagr_5y"] == pytest.approx(0.1702, abs=0.001)

    def test_calculate_fcff_cagr_5y(self, calculator, sample_data):
        """测试FCF 5年复合增长率"""
        result = calculator.calculate(**sample_data)
        # CAGR = (100000/60000)^(1/4) - 1 = 0.1362
        assert result["fcff_cagr_5y"] == pytest.approx(0.1362, abs=0.001)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_growth.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/growth.py
"""成长能力计算器"""
import math
from typing import Any

from .base import BaseCalculator


class GrowthCalculator(BaseCalculator):
    """成长能力计算器"""

    @staticmethod
    def _calculate_cagr(start_value: float, end_value: float, years: int) -> float | None:
        """计算复合增长率"""
        if start_value is None or end_value is None or start_value <= 0 or end_value <= 0:
            return None
        if years <= 0:
            return None
        return (end_value / start_value) ** (1 / years) - 1

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """
        计算成长能力指标

        指标:
        - revenue_growth_1y: 收入增长率(1年)
        - profit_growth_1y: 利润增长率(1年)
        - revenue_cagr_5y: 收入5年复合增长率
        - profit_cagr_5y: 利润5年复合增长率
        - fcff_cagr_5y: FCF 5年复合增长率
        """
        result = {}

        # 获取基础数据
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        prev_total_revenue = self._safe_float(profit_sheet.get("prev_total_revenue"))
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        prev_net_profit = self._safe_float(profit_sheet.get("prev_net_profit"))
        revenue_history = profit_sheet.get("revenue_history", [])
        profit_history = profit_sheet.get("profit_history", [])
        fcff_history = profit_sheet.get("fcff_history", [])

        # 收入增长率(1年)
        if (
            total_revenue is not None
            and prev_total_revenue is not None
            and prev_total_revenue != 0
        ):
            result["revenue_growth_1y"] = self._round(
                (total_revenue - prev_total_revenue) / prev_total_revenue
            )
        else:
            result["revenue_growth_1y"] = None

        # 利润增长率(1年)
        if net_profit is not None and prev_net_profit is not None and prev_net_profit != 0:
            result["profit_growth_1y"] = self._round(
                (net_profit - prev_net_profit) / prev_net_profit
            )
        else:
            result["profit_growth_1y"] = None

        # 收入5年复合增长率
        if len(revenue_history) >= 5:
            cagr = self._calculate_cagr(revenue_history[0], revenue_history[-1], 4)
            result["revenue_cagr_5y"] = self._round(cagr) if cagr is not None else None
        else:
            result["revenue_cagr_5y"] = None

        # 利润5年复合增长率
        if len(profit_history) >= 5:
            cagr = self._calculate_cagr(profit_history[0], profit_history[-1], 4)
            result["profit_cagr_5y"] = self._round(cagr) if cagr is not None else None
        else:
            result["profit_cagr_5y"] = None

        # FCF 5年复合增长率
        if len(fcff_history) >= 5:
            cagr = self._calculate_cagr(fcff_history[0], fcff_history[-1], 4)
            result["fcff_cagr_5y"] = self._round(cagr) if cagr is not None else None
        else:
            result["fcff_cagr_5y"] = None

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_growth.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/growth.py tests/calculators/test_growth.py
git commit -m "feat: 添加成长能力计算器"
```

---

## Task 7: 实现估值指标计算器

**Files:**
- Create: `src/ecox/calculators/valuation.py`
- Create: `tests/calculators/test_valuation.py`

**Step 1: Write the failing test**

```python
# tests/calculators/test_valuation.py
"""估值指标计算器测试"""
import pytest

from ecox.calculators.valuation import ValuationCalculator


class TestValuationCalculator:
    """估值指标计算器测试"""

    @pytest.fixture
    def calculator(self):
        return ValuationCalculator()

    @pytest.fixture
    def sample_data(self):
        return {
            "profit_sheet": {
                "net_profit": 150000,
                "total_revenue": 1000000,
            },
            "balance_sheet": {
                "owner_equity": 3000000,
            },
            "cash_flow_sheet": {},
            "market_data": {
                "market_cap": 5000000,  # 市值
                "total_debt": 2000000,  # 总债务
                "cash": 500000,  # 现金
                "ebitda": 300000,  # EBITDA
                "earnings_growth": 0.20,  # 利润增长率
            },
        }

    def test_calculate_pe_ratio(self, calculator, sample_data):
        """测试市盈率"""
        result = calculator.calculate(**sample_data)
        # PE = 市值 / 净利润 = 5000000 / 150000 = 33.33
        assert result["pe_ratio"] == pytest.approx(33.3333, abs=0.01)

    def test_calculate_pb_ratio(self, calculator, sample_data):
        """测试市净率"""
        result = calculator.calculate(**sample_data)
        # PB = 市值 / 净资产 = 5000000 / 3000000 = 1.6667
        assert result["pb_ratio"] == pytest.approx(1.6667, abs=0.01)

    def test_calculate_ps_ratio(self, calculator, sample_data):
        """测试市销率"""
        result = calculator.calculate(**sample_data)
        # PS = 市值 / 营收 = 5000000 / 1000000 = 5.0
        assert result["ps_ratio"] == 5.0000

    def test_calculate_ev_ebitda(self, calculator, sample_data):
        """测试EV/EBITDA"""
        result = calculator.calculate(**sample_data)
        # EV = 市值 + 债务 - 现金 = 5000000 + 2000000 - 500000 = 6500000
        # EV/EBITDA = 6500000 / 300000 = 21.6667
        assert result["ev_ebitda"] == pytest.approx(21.6667, abs=0.01)

    def test_calculate_peg_ratio(self, calculator, sample_data):
        """测试PEG"""
        result = calculator.calculate(**sample_data)
        # PEG = PE / 增长率 = 33.33 / 20 = 1.6667
        assert result["peg_ratio"] == pytest.approx(1.6667, abs=0.01)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calculators/test_valuation.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/calculators/valuation.py
"""估值指标计算器"""
from typing import Any

from .base import BaseCalculator


class ValuationCalculator(BaseCalculator):
    """估值指标计算器"""

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """
        计算估值指标

        指标:
        - pe_ratio: 市盈率 = 市值 / 净利润
        - pb_ratio: 市净率 = 市值 / 净资产
        - ps_ratio: 市销率 = 市值 / 营收
        - ev_ebitda: EV/EBITDA
        - peg_ratio: PEG = PE / 增长率
        """
        result = {}
        market_data = market_data or {}

        # 获取基础数据
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        owner_equity = self._safe_float(balance_sheet.get("owner_equity"))
        market_cap = self._safe_float(market_data.get("market_cap"))
        total_debt = self._safe_float(market_data.get("total_debt")) or 0
        cash = self._safe_float(market_data.get("cash")) or 0
        ebitda = self._safe_float(market_data.get("ebitda"))
        earnings_growth = self._safe_float(market_data.get("earnings_growth"))

        # PE
        if market_cap is not None and net_profit is not None and net_profit != 0:
            result["pe_ratio"] = self._round(market_cap / net_profit)
        else:
            result["pe_ratio"] = None

        # PB
        if market_cap is not None and owner_equity is not None and owner_equity != 0:
            result["pb_ratio"] = self._round(market_cap / owner_equity)
        else:
            result["pb_ratio"] = None

        # PS
        if market_cap is not None and total_revenue is not None and total_revenue != 0:
            result["ps_ratio"] = self._round(market_cap / total_revenue)
        else:
            result["ps_ratio"] = None

        # EV/EBITDA
        if market_cap is not None and ebitda is not None and ebitda != 0:
            ev = market_cap + total_debt - cash
            result["ev_ebitda"] = self._round(ev / ebitda)
        else:
            result["ev_ebitda"] = None

        # PEG
        if (
            result["pe_ratio"] is not None
            and earnings_growth is not None
            and earnings_growth != 0
        ):
            # 增长率需要转换为百分比形式 (如 0.20 -> 20)
            result["peg_ratio"] = self._round(result["pe_ratio"] / (earnings_growth * 100))
        else:
            result["peg_ratio"] = None

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calculators/test_valuation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/calculators/valuation.py tests/calculators/test_valuation.py
git commit -m "feat: 添加估值指标计算器"
```

---

## Task 8: 更新计算器模块导出

**Files:**
- Modify: `src/ecox/calculators/__init__.py`

**Step 1: Update __init__.py**

```python
# src/ecox/calculators/__init__.py
"""财务指标计算器模块"""
from .base import BaseCalculator
from .profitability import ProfitabilityCalculator
from .cash_flow import CashFlowCalculator
from .solvency import SolvencyCalculator
from .efficiency import EfficiencyCalculator
from .growth import GrowthCalculator
from .valuation import ValuationCalculator

__all__ = [
    "BaseCalculator",
    "ProfitabilityCalculator",
    "CashFlowCalculator",
    "SolvencyCalculator",
    "EfficiencyCalculator",
    "GrowthCalculator",
    "ValuationCalculator",
]
```

**Step 2: Run all calculator tests**

Run: `uv run pytest tests/calculators/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add src/ecox/calculators/__init__.py
git commit -m "feat: 导出所有计算器"
```

---

## Task 9: 创建 StockFinancialMetrics 数据模型

**Files:**
- Modify: `src/ecox/models/__init__.py`

**Step 1: Add model to __init__.py**

在 `src/ecox/models/__init__.py` 中添加 `StockFinancialMetrics` 类：

```python
# 在文件末尾 __all__ 列表之前添加

class StockFinancialMetrics(Base):
    """统一财务指标表"""
    __tablename__ = "stock_financial_metrics"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    report_date = Column(String(20), nullable=False, index=True)
    report_type = Column(String(10))

    # === 盈利能力 ===
    roe = Column(Numeric(10, 4))
    roa = Column(Numeric(10, 4))
    roic = Column(Numeric(10, 4))
    gross_margin = Column(Numeric(10, 4))
    net_margin = Column(Numeric(10, 4))
    operating_margin = Column(Numeric(10, 4))

    # === 现金流分析 ===
    fcff = Column(Numeric(20, 4))
    fcfe = Column(Numeric(20, 4))
    capex = Column(Numeric(20, 4))
    cash_conversion_rate = Column(Numeric(10, 4))
    ocf_to_sales = Column(Numeric(10, 4))

    # === 偿债能力 ===
    debt_ratio = Column(Numeric(10, 4))
    current_ratio = Column(Numeric(10, 4))
    quick_ratio = Column(Numeric(10, 4))
    interest_coverage = Column(Numeric(10, 4))

    # === 营运能力 ===
    inventory_turnover = Column(Numeric(10, 4))
    receivables_turnover = Column(Numeric(10, 4))
    asset_turnover = Column(Numeric(10, 4))

    # === 成长能力 ===
    revenue_growth_1y = Column(Numeric(10, 4))
    profit_growth_1y = Column(Numeric(10, 4))
    revenue_cagr_5y = Column(Numeric(10, 4))
    profit_cagr_5y = Column(Numeric(10, 4))
    fcff_cagr_5y = Column(Numeric(10, 4))

    # === 估值指标 ===
    pe_ratio = Column(Numeric(10, 4))
    pb_ratio = Column(Numeric(10, 4))
    ps_ratio = Column(Numeric(10, 4))
    ev_ebitda = Column(Numeric(10, 4))
    peg_ratio = Column(Numeric(10, 4))

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_financial_metrics"),
    )

    def __repr__(self):
        return f"<StockFinancialMetrics({self.stock_code} {self.report_date})>"


# 更新 __all__ 列表
__all__ = [
    "Base",
    "StockRealTime",
    "StockBasic",
    "StockDailyData",
    "StockValuation",
    "IndustryValuation",
    "StockProfitSheet",
    "StockBalanceSheet",
    "StockCashFlowSheet",
    "UpdateLog",
    "StockPrice",
    "DataAlert",
    "StockFinancialMetrics",  # 新增
]
```

**Step 2: Run existing tests**

Run: `uv run pytest tests/ -v --ignore=tests/integration`
Expected: All PASS

**Step 3: Commit**

```bash
git add src/ecox/models/__init__.py
git commit -m "feat: 添加 StockFinancialMetrics 数据模型"
```

---

## Task 10: 实现统一财务分析服务

**Files:**
- Create: `src/ecox/services/financial_analysis_service.py`
- Create: `tests/services/test_financial_analysis_service.py`

**Step 1: Write the failing test**

```python
# tests/services/test_financial_analysis_service.py
"""统一财务分析服务测试"""
import pytest
from unittest.mock import patch, MagicMock

from ecox.services.financial_analysis_service import FinancialAnalysisService


class TestFinancialAnalysisService:
    """统一财务分析服务测试"""

    @pytest.fixture
    def service(self):
        return FinancialAnalysisService()

    @pytest.fixture
    def sample_financial_data(self):
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "operating_profit": 200000,
                "net_profit": 150000,
                "operating_cost": 400000,
                "interest_expense": 10000,
            },
            "balance_sheet": {
                "total_assets": 5000000,
                "total_liabilities": 2000000,
                "owner_equity": 3000000,
                "current_assets": 1500000,
                "current_liabilities": 800000,
                "inventory": 300000,
                "accounts_receivable": 200000,
            },
            "cash_flow_sheet": {
                "operating_cash_flow": 200000,
                "capex": 50000,
            },
        }

    def test_service_has_all_calculators(self, service):
        """测试服务包含所有计算器"""
        assert "profitability" in service.calculators
        assert "cash_flow" in service.calculators
        assert "solvency" in service.calculators
        assert "efficiency" in service.calculators
        assert "growth" in service.calculators
        assert "valuation" in service.calculators

    def test_calculate_all_modules(self, service, sample_financial_data):
        """测试计算所有模块"""
        with patch.object(service, '_get_financial_data', return_value=sample_financial_data):
            result = service.calculate_metrics("600809")

        assert "profitability" in result
        assert "cash_flow" in result
        assert "solvency" in result
        assert "efficiency" in result
        # growth 和 valuation 需要额外数据，可能为空

    def test_calculate_specific_modules(self, service, sample_financial_data):
        """测试计算指定模块"""
        with patch.object(service, '_get_financial_data', return_value=sample_financial_data):
            result = service.calculate_metrics(
                "600809",
                modules=["profitability", "cash_flow"]
            )

        assert "profitability" in result
        assert "cash_flow" in result
        assert "solvency" not in result

    def test_calculate_profitability_metrics(self, service, sample_financial_data):
        """测试盈利能力指标计算"""
        with patch.object(service, '_get_financial_data', return_value=sample_financial_data):
            result = service.calculate_metrics("600809", modules=["profitability"])

        assert result["profitability"]["roe"] == 0.0500
        assert result["profitability"]["roa"] == 0.0300
        assert result["profitability"]["net_margin"] == 0.1500
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_financial_analysis_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/ecox/services/financial_analysis_service.py
"""统一财务分析服务"""
import logging
from typing import Any

from ..calculators import (
    ProfitabilityCalculator,
    CashFlowCalculator,
    SolvencyCalculator,
    EfficiencyCalculator,
    GrowthCalculator,
    ValuationCalculator,
)
from ..database import get_db_session
from .. import models

logger = logging.getLogger(__name__)


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

    def _get_financial_data(
        self, stock_code: str, report_date: str | None = None
    ) -> dict[str, Any]:
        """
        获取财务数据（优先数据库，缺失时从 akshare 补充）

        Args:
            stock_code: 股票代码
            report_date: 报告日期

        Returns:
            包含三大报表数据的字典
        """
        profit_sheet = {}
        balance_sheet = {}
        cash_flow_sheet = {}

        with get_db_session() as session:
            # 获取利润表
            profit_query = session.query(models.StockProfitSheet).filter(
                models.StockProfitSheet.stock_code == stock_code
            )
            if report_date:
                profit_query = profit_query.filter(
                    models.StockProfitSheet.report_date == report_date
                )
            profit_record = profit_query.order_by(
                models.StockProfitSheet.report_date.desc()
            ).first()

            if profit_record:
                profit_sheet = {
                    "total_revenue": float(profit_record.total_revenue or 0),
                    "operating_profit": float(profit_record.operating_profit or 0),
                    "net_profit": float(profit_record.net_profit or 0),
                    "basic_eps": float(profit_record.basic_eps or 0),
                }
                if profit_record.extra_data:
                    profit_sheet.update(profit_record.extra_data)

            # 获取资产负债表
            balance_query = session.query(models.StockBalanceSheet).filter(
                models.StockBalanceSheet.stock_code == stock_code
            )
            if report_date:
                balance_query = balance_query.filter(
                    models.StockBalanceSheet.report_date == report_date
                )
            balance_record = balance_query.order_by(
                models.StockBalanceSheet.report_date.desc()
            ).first()

            if balance_record:
                balance_sheet = {
                    "total_assets": float(balance_record.total_assets or 0),
                    "total_liabilities": float(balance_record.total_liabilities or 0),
                    "owner_equity": float(balance_record.owner_equity or 0),
                }
                if balance_record.extra_data:
                    balance_sheet.update(balance_record.extra_data)

            # 获取现金流量表
            cashflow_query = session.query(models.StockCashFlowSheet).filter(
                models.StockCashFlowSheet.stock_code == stock_code
            )
            if report_date:
                cashflow_query = cashflow_query.filter(
                    models.StockCashFlowSheet.report_date == report_date
                )
            cashflow_record = cashflow_query.order_by(
                models.StockCashFlowSheet.report_date.desc()
            ).first()

            if cashflow_record:
                cash_flow_sheet = {
                    "operating_cash_flow": float(cashflow_record.operating_cash_flow or 0),
                    "investing_cash_flow": float(cashflow_record.investing_cash_flow or 0),
                    "financing_cash_flow": float(cashflow_record.financing_cash_flow or 0),
                }
                if cashflow_record.extra_data:
                    cash_flow_sheet.update(cashflow_record.extra_data)

        return {
            "profit_sheet": profit_sheet,
            "balance_sheet": balance_sheet,
            "cash_flow_sheet": cash_flow_sheet,
        }

    def calculate_metrics(
        self,
        stock_code: str,
        report_date: str | None = None,
        modules: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        计算财务指标

        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，默认最新）
            modules: 计算模块列表（可选，默认全部）

        Returns:
            完整的财务指标结果
        """
        # 获取财务数据
        financial_data = self._get_financial_data(stock_code, report_date)

        # 确定要计算的模块
        if modules is None:
            modules = list(self.calculators.keys())

        result = {
            "stock_code": stock_code,
            "report_date": report_date,
        }

        # 调用各计算器
        for module_name in modules:
            if module_name in self.calculators:
                try:
                    calculator = self.calculators[module_name]
                    result[module_name] = calculator.calculate(
                        profit_sheet=financial_data["profit_sheet"],
                        balance_sheet=financial_data["balance_sheet"],
                        cash_flow_sheet=financial_data["cash_flow_sheet"],
                        market_data=None,  # 估值指标需要额外处理
                    )
                except Exception as e:
                    logger.error(f"计算 {module_name} 失败: {e}")
                    result[module_name] = {}

        return result

    def save_metrics(self, stock_code: str, metrics: dict) -> bool:
        """保存计算结果到数据库"""
        try:
            with get_db_session() as session:
                # 检查是否存在
                existing = session.query(models.StockFinancialMetrics).filter(
                    models.StockFinancialMetrics.stock_code == stock_code,
                    models.StockFinancialMetrics.report_date == metrics.get("report_date"),
                ).first()

                if existing:
                    # 更新
                    self._update_metrics_record(existing, metrics)
                else:
                    # 新增
                    record = models.StockFinancialMetrics(
                        stock_code=stock_code,
                        stock_name=metrics.get("stock_name"),
                        report_date=metrics.get("report_date"),
                        report_type=metrics.get("report_type"),
                    )
                    self._update_metrics_record(record, metrics)
                    session.add(record)

                session.commit()
            return True
        except Exception as e:
            logger.error(f"保存指标失败: {e}")
            return False

    def _update_metrics_record(self, record, metrics: dict):
        """更新指标记录"""
        # 盈利能力
        if "profitability" in metrics:
            p = metrics["profitability"]
            record.roe = p.get("roe")
            record.roa = p.get("roa")
            record.roic = p.get("roic")
            record.gross_margin = p.get("gross_margin")
            record.net_margin = p.get("net_margin")
            record.operating_margin = p.get("operating_margin")

        # 现金流
        if "cash_flow" in metrics:
            c = metrics["cash_flow"]
            record.fcff = c.get("fcff")
            record.fcfe = c.get("fcfe")
            record.capex = c.get("capex")
            record.cash_conversion_rate = c.get("cash_conversion_rate")
            record.ocf_to_sales = c.get("ocf_to_sales")

        # 偿债能力
        if "solvency" in metrics:
            s = metrics["solvency"]
            record.debt_ratio = s.get("debt_ratio")
            record.current_ratio = s.get("current_ratio")
            record.quick_ratio = s.get("quick_ratio")
            record.interest_coverage = s.get("interest_coverage")

        # 营运能力
        if "efficiency" in metrics:
            e = metrics["efficiency"]
            record.inventory_turnover = e.get("inventory_turnover")
            record.receivables_turnover = e.get("receivables_turnover")
            record.asset_turnover = e.get("asset_turnover")

        # 成长能力
        if "growth" in metrics:
            g = metrics["growth"]
            record.revenue_growth_1y = g.get("revenue_growth_1y")
            record.profit_growth_1y = g.get("profit_growth_1y")
            record.revenue_cagr_5y = g.get("revenue_cagr_5y")
            record.profit_cagr_5y = g.get("profit_cagr_5y")
            record.fcff_cagr_5y = g.get("fcff_cagr_5y")

        # 估值指标
        if "valuation" in metrics:
            v = metrics["valuation"]
            record.pe_ratio = v.get("pe_ratio")
            record.pb_ratio = v.get("pb_ratio")
            record.ps_ratio = v.get("ps_ratio")
            record.ev_ebitda = v.get("ev_ebitda")
            record.peg_ratio = v.get("peg_ratio")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_financial_analysis_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ecox/services/financial_analysis_service.py tests/services/test_financial_analysis_service.py
git commit -m "feat: 添加统一财务分析服务"
```

---

## Task 11: 添加 MCP 工具

**Files:**
- Modify: `src/ecox/get_data.py`

**Step 1: Add import and tool**

在 `src/ecox/get_data.py` 中添加：

```python
# 在文件开头的导入部分添加
from ecox.services.financial_analysis_service import FinancialAnalysisService
import json

# 在文件中添加新工具（在 get_sql_data 函数之后）

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
    try:
        # 格式化股票代码
        formatted_code = code_format(stock_code)

        # 创建服务实例
        service = FinancialAnalysisService()

        # 计算指标
        result = service.calculate_metrics(
            stock_code=formatted_code,
            report_date=report_date,
            modules=modules,
        )

        # 添加元信息
        result["source"] = "database"
        result["update_time"] = datetime.now().isoformat()

        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v --ignore=tests/integration`
Expected: All PASS

**Step 3: Commit**

```bash
git add src/ecox/get_data.py
git commit -m "feat: 添加 get_financial_analysis MCP 工具"
```

---

## Task 12: 运行完整测试套件

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v --ignore=tests/integration`
Expected: All PASS

**Step 2: Run with coverage**

Run: `uv run pytest tests/ --cov=src/ecox --cov-report=term-missing --ignore=tests/integration`
Expected: Coverage report

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: 完成统一财务分析模型实现

- 6大分析维度计算器
- StockFinancialMetrics 数据模型
- FinancialAnalysisService 统一服务
- get_financial_analysis MCP 工具"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | 计算器基类 | `calculators/base.py`, `test_base.py` |
| 2 | 盈利能力计算器 | `calculators/profitability.py`, `test_profitability.py` |
| 3 | 现金流计算器 | `calculators/cash_flow.py`, `test_cash_flow.py` |
| 4 | 偿债能力计算器 | `calculators/solvency.py`, `test_solvency.py` |
| 5 | 营运能力计算器 | `calculators/efficiency.py`, `test_efficiency.py` |
| 6 | 成长能力计算器 | `calculators/growth.py`, `test_growth.py` |
| 7 | 估值指标计算器 | `calculators/valuation.py`, `test_valuation.py` |
| 8 | 更新模块导出 | `calculators/__init__.py` |
| 9 | 数据模型 | `models/__init__.py` |
| 10 | 分析服务 | `services/financial_analysis_service.py`, `test_financial_analysis_service.py` |
| 11 | MCP 工具 | `get_data.py` |
| 12 | 完整测试 | - |
