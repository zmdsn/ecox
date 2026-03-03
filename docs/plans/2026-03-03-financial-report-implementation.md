# 三大报表下载服务实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 下载所有 A 股的三大财报数据并存储到数据库，支持首次全量和每日增量更新

**架构:** 创建独立的 FinancialReportService，使用核心字段 + JSON 存储混合方案，集成数据验证

**技术栈:** Python 3.13, SQLAlchemy, akshare, pytest

---

## Task 1: 扩展数据库模型

**Files:**
- Modify: `src/ecox/models/__init__.py`

**Step 1: 读取现有模型**

Read the existing StockProfitSheet, StockBalanceSheet, StockCashFlowSheet models to understand current structure.

Run: `grep -n "class Stock.*Sheet" src/ecox/models/__init__.py`

Expected: Find existing model definitions around lines 146-204

**Step 2: 添加 JSON 列导入**

At the top of the file, add JSON to the imports:

```python
from sqlalchemy.dialects.postgresql import JSON
```

**Step 3: 扩展 StockProfitSheet 模型**

Replace the existing StockProfitSheet class (around line 146-164) with:

```python
class StockProfitSheet(Base):
    """利润表 - 扩展版"""

    __tablename__ = "stock_profit_sheet"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20), index=True)
    report_type = Column(String(10))

    # 核心指标（独立列）
    total_revenue = Column(Numeric(20, 2))
    operating_profit = Column(Numeric(20, 2))
    net_profit = Column(Numeric(20, 2))
    basic_eps = Column(Numeric(10, 4))

    # 完整数据（JSON 存储）
    extra_data = Column(JSON)

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_profit_report"),
    )

    def __repr__(self):
        return f"<StockProfitSheet({self.stock_code} {self.report_date})>"
```

**Step 4: 扩展 StockBalanceSheet 模型**

Replace the existing StockBalanceSheet class (around line 167-184) with:

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
    total_assets = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    owner_equity = Column(Numeric(20, 2))

    extra_data = Column(JSON)

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_balance_report"),
    )

    def __repr__(self):
        return f"<StockBalanceSheet({self.stock_code} {self.report_date})>"
```

**Step 5: 扩展 StockCashFlowSheet 模型**

Replace the existing StockCashFlowSheet class (around line 187-204) with:

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
    operating_cash_flow = Column(Numeric(20, 2))
    investing_cash_flow = Column(Numeric(20, 2))
    financing_cash_flow = Column(Numeric(20, 2))

    extra_data = Column(JSON)

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_cashflow_report"),
    )

    def __repr__(self):
        return f"<StockCashFlowSheet({self.stock_code} {self.report_date})>"
```

**Step 6: 验证模型导入**

Run: `uv run python -c "from ecox.models import StockProfitSheet, StockBalanceSheet, StockCashFlowSheet; print('Models imported successfully')"`

Expected: `Models imported successfully`

**Step 7: Commit**

```bash
git add src/ecox/models/__init__.py
git commit -m "feat: 扩展三大报表模型添加 JSON 字段

- 添加 extra_data JSON 字段存储完整财报数据
- 添加 update_time 字段
- 添加唯一约束 (stock_code + report_date)
- 保持核心字段作为独立列"
```

---

## Task 2: 创建数据库迁移

**Files:**
- Create: `src/ecox/alembic/versions/xxxx_add_report_extra_fields.py`

**Step 1: 生成迁移文件**

Run: `uv run alembic revision -m "add report extra fields and constraints"`

Expected: New migration file created in `src/ecox/alembic/versions/`

**Step 2: 编辑迁移文件**

Edit the generated migration file to add the upgrades:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = 'xxxx'
down_revision = 'yyyy'  # Replace with previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to stock_profit_sheet
    op.add_column('stock_profit_sheet', sa.Column('extra_data', JSON(), nullable=True))
    op.add_column('stock_profit_sheet', sa.Column('update_time', sa.DateTime(), nullable=True))

    # Add columns to stock_balance_sheet
    op.add_column('stock_balance_sheet', sa.Column('extra_data', JSON(), nullable=True))
    op.add_column('stock_balance_sheet', sa.Column('update_time', sa.DateTime(), nullable=True))

    # Add columns to stock_cash_flow_sheet
    op.add_column('stock_cash_flow_sheet', sa.Column('extra_data', JSON(), nullable=True))
    op.add_column('stock_cash_flow_sheet', sa.Column('update_time', sa.DateTime(), nullable=True))

    # Create unique constraints
    op.create_unique_constraint('uix_profit_report', 'stock_profit_sheet', ['stock_code', 'report_date'])
    op.create_unique_constraint('uix_balance_report', 'stock_balance_sheet', ['stock_code', 'report_date'])
    op.create_unique_constraint('uix_cashflow_report', 'stock_cash_flow_sheet', ['stock_code', 'report_date'])


def downgrade():
    # Drop unique constraints
    op.drop_constraint('uix_cashflow_report', 'stock_cash_flow_sheet')
    op.drop_constraint('uix_balance_report', 'stock_balance_sheet')
    op.drop_constraint('uix_profit_report', 'stock_profit_sheet')

    # Drop columns from stock_cash_flow_sheet
    op.drop_column('stock_cash_flow_sheet', 'update_time')
    op.drop_column('stock_cash_flow_sheet', 'extra_data')

    # Drop columns from stock_balance_sheet
    op.drop_column('stock_balance_sheet', 'update_time')
    op.drop_column('stock_balance_sheet', 'extra_data')

    # Drop columns from stock_profit_sheet
    op.drop_column('stock_profit_sheet', 'update_time')
    op.drop_column('stock_profit_sheet', 'extra_data')
```

**Step 3: 运行迁移**

Run: `uv run alembic upgrade head`

Expected: `Running upgrade... OK`

**Step 4: 验证表结构**

Run: `uv run python -c "from ecox.database import init_db; db = init_db(); print('Columns:', [c['name'] for c in db.dialect.get_columns(db.connect(), 'stock_profit_sheet')])"`

Expected: Should see `extra_data` and `update_time` in the column list

**Step 5: Commit**

```bash
git add src/ecox/alembic/versions/
git commit -m "feat: 添加三大报表扩展字段迁移

- 添加 extra_data JSON 列
- 添加 update_time 列
- 添加唯一约束"
```

---

## Task 3: 创建财报验证器

**Files:**
- Create: `src/ecox/validators/report_validator.py`
- Create: `tests/validators/test_report_validator.py`

**Step 1: 编写测试用例（TDD - 先写测试）**

Create `tests/validators/test_report_validator.py`:

```python
"""财报验证器测试"""
import pytest
from ecox.validators.report_validator import ReportValidator


class TestReportValidator:
    """财报验证器测试"""

    def test_validate_profit_sheet_valid_data(self):
        """测试有效利润表数据"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "stock_name": "测试股票",
            "report_date": "20240930",
            "total_revenue": 1000000000,
            "net_profit": 50000000,
        }
        result = validator.validate_profit_sheet(data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_profit_sheet_negative_revenue(self):
        """测试营业收入为负"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
            "total_revenue": -1000,
        }
        result = validator.validate_profit_sheet(data)

        assert result.is_valid is False
        assert any("negative" in err.lower() or "为负" in err for err in result.errors)

    def test_validate_profit_sheet_missing_core_field(self):
        """测试核心字段缺失"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
        }
        result = validator.validate_profit_sheet(data)

        assert result.is_valid is False

    def test_validate_balance_sheet_equity_check(self):
        """测试资产负债表勾稽关系"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
            "total_assets": 1000000000,
            "total_liabilities": 300000000,
            "owner_equity": 700000000,
        }
        result = validator.validate_balance_sheet(data)

        # 勾稽关系正确 (资产 = 负债 + 权益)
        assert result.is_valid is True

    def test_validate_balance_sheet_equity_mismatch(self):
        """测试资产负债表勾稽关系不匹配"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
            "total_assets": 1000000000,
            "total_liabilities": 300000000,
            "owner_equity": 500000000,  # 不匹配，应该是 700000000
        }
        result = validator.validate_balance_sheet(data)

        # 勾稽关系不匹配，但应该产生警告而非错误
        assert result.is_valid is True  # 仍然有效
        assert len(result.warnings) > 0
```

**Step 2: 运行测试验证失败**

Run: `uv run pytest tests/validators/test_report_validator.py -v`

Expected: `ImportError: cannot import name 'ReportValidator'`

**Step 3: 实现 ReportValidator**

Create `src/ecox/validators/report_validator.py`:

```python
"""财报验证器"""
import math
from typing import Dict, Any

from .result import ValidationResult


class ReportValidator:
    """财报数据验证器"""

    def __init__(self):
        pass

    def validate_profit_sheet(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证利润表数据

        验证规则：
        - 核心字段非负
        - 核心字段不能为空
        - 不允许 NaN 值
        """
        result = ValidationResult(is_valid=True)

        # 检查核心字段
        core_fields = {
            "total_revenue": "营业总收入",
            "operating_profit": "营业利润",
            "net_profit": "净利润",
        }

        for field, name in core_fields.items():
            value = data.get(field)

            # 检查字段存在
            if value is None:
                continue  # 可选字段

            # 检查 NaN
            if isinstance(value, float) and math.isnan(value):
                result.add_error(f"{name} 为 NaN")
                continue

            # 检查非负
            try:
                num_value = float(value)
                if num_value < 0:
                    result.add_error(f"{name} 为负值: {num_value}")
            except (ValueError, TypeError):
                result.add_error(f"{name} 格式错误: {value}")

        return result

    def validate_balance_sheet(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证资产负债表数据

        验证规则：
        - 核心字段非负
        - 勾稽关系检查（资产 = 负债 + 权益）
        """
        result = ValidationResult(is_valid=True)

        # 检查核心字段非负
        core_fields = {
            "total_assets": "总资产",
            "total_liabilities": "总负债",
            "owner_equity": "所有者权益",
        }

        for field, name in core_fields.items():
            value = data.get(field)

            if value is None:
                continue

            if isinstance(value, float) and math.isnan(value):
                result.add_error(f"{name} 为 NaN")
                continue

            try:
                num_value = float(value)
                if num_value < 0:
                    result.add_error(f"{name} 为负值: {num_value}")
            except (ValueError, TypeError):
                result.add_error(f"{name} 格式错误: {value}")

        # 勾稽关系检查（资产 = 负债 + 权益）
        assets = data.get("total_assets")
        liabilities = data.get("total_liabilities")
        equity = data.get("owner_equity")

        if all(v is not None for v in [assets, liabilities, equity]):
            try:
                assets_val = float(assets)
                liabilities_val = float(liabilities)
                equity_val = float(equity)

                if not any(math.isnan(v) for v in [assets_val, liabilities_val, equity_val]):
                    calculated = liabilities_val + equity_val
                    # 允许 1% 的误差
                    tolerance = max(abs(assets_val) * 0.01, 1000)
                    if abs(assets_val - calculated) > tolerance:
                        result.add_warning(
                            f"勾稽关系不匹配: 资产({assets_val:.0f}) != "
                            f"负债({liabilities_val:.0f}) + 权益({equity_val:.0f})"
                        )
            except (ValueError, TypeError):
                pass

        return result

    def validate_cash_flow_sheet(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证现金流量表数据

        验证规则：
        - 核心字段可以为负（现金流可能是负数）
        - 不允许 NaN 值
        """
        result = ValidationResult(is_valid=True)

        # 现金流量表的值可以为负，只检查 NaN
        core_fields = {
            "operating_cash_flow": "经营活动现金流",
            "investing_cash_flow": "投资活动现金流",
            "financing_cash_flow": "筹资活动现金流",
        }

        for field, name in core_fields.items():
            value = data.get(field)

            if value is None:
                continue

            if isinstance(value, float) and math.isnan(value):
                result.add_error(f"{name} 为 NaN")
            elif not isinstance(value, (int, float)):
                result.add_error(f"{name} 格式错误: {value}")

        return result
```

**Step 4: 更新 validators/__init__.py**

Add to `src/ecox/validators/__init__.py`:

```python
from .report_validator import ReportValidator

__all__ = [
    "ValidationResult",
    "DataValidator",
    "PriceValidator",
    "VolumeValidator",
    "CompositeValidator",
    "ReportValidator",  # 新增
]
```

**Step 5: 运行测试验证通过**

Run: `uv run pytest tests/validators/test_report_validator.py -v`

Expected: 所有测试通过

**Step 6: Commit**

```bash
git add src/ecox/validators/ tests/validators/
git commit -m "feat: 添加财报验证器 ReportValidator

- 验证利润表核心字段非负
- 验证资产负债表勾稽关系
- 验证现金流量表 NaN 值
- 添加完整单元测试"
```

---

## Task 4: 创建财报下载服务基础类

**Files:**
- Create: `src/ecox/services/financial_report_service.py`
- Update: `src/ecox/services/__init__.py`

**Step 1: 编写服务类基础结构**

Create `src/ecox/services/financial_report_service.py`:

```python
"""财务报表下载服务"""
import time
import logging
from typing import List, Dict, Optional
import akshare as ak

from ..database import get_db_session
from .. import models
from ..validators.report_validator import ReportValidator
from .alert_service import AlertService

logger = logging.getLogger(__name__)


class FinancialReportService:
    """财务报表下载服务"""

    def __init__(self):
        self.validator = ReportValidator()
        self.alert_service = AlertService()

    def _get_stock_list(self) -> List[str]:
        """获取所有股票代码"""
        with get_db_session() as session:
            stocks = session.query(
                models.StockBasic.stock_code
            ).all()
            return [s.stock_code for s in stocks]

    def _code_format(self, code: str) -> str:
        """格式化股票代码为 akshare 格式"""
        code = code.replace("SH", "").replace("SZ", "")
        if code.startswith("6"):
            return f"SH{code}"
        else:
            return f"SZ{code}"
```

**Step 2: 添加利润表下载方法**

Add to `FinancialReportService` class:

```python
    def fetch_profit_sheet(self, stock_code: str) -> List[Dict]:
        """
        下载利润表数据

        Args:
            stock_code: 股票代码（如 "600809"）

        Returns:
            利润表数据列表
        """
        try:
            symbol = self._code_format(stock_code)
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol)

            if df.empty:
                logger.warning(f"股票 {stock_code} 无利润表数据")
                return []

            # 转换为字典列表
            data_list = []
            for _, row in df.iterrows():
                # 提取核心字段
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("股票简称", ""),
                    "report_date": str(row.get("报告日期", "")),
                    "report_type": str(row.get("报告类型", "")),
                    # 核心指标
                    "total_revenue": self._safe_float(row.get("营业总收入")),
                    "operating_profit": self._safe_float(row.get("营业利润")),
                    "net_profit": self._safe_float(row.get("净利润")),
                    "basic_eps": self._safe_float(row.get("基本每股收益")),
                }

                # 完整数据存入 JSON
                extra_data = {}
                for col in df.columns:
                    if col not in ["股票简称", "报告日期", "报告类型"]:
                        extra_data[col] = row.get(col)
                item["extra_data"] = extra_data

                data_list.append(item)

            logger.info(f"股票 {stock_code} 下载利润表 {len(data_list)} 条记录")
            return data_list

        except Exception as e:
            logger.error(f"下载 {stock_code} 利润表失败: {e}")
            return []

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
```

**Step 3: 添加资产负债表下载方法**

Add to `FinancialReportService` class:

```python
    def fetch_balance_sheet(self, stock_code: str) -> List[Dict]:
        """
        下载资产负债表数据

        Args:
            stock_code: 股票代码

        Returns:
            资产负债表数据列表
        """
        try:
            symbol = self._code_format(stock_code)
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol)

            if df.empty:
                logger.warning(f"股票 {stock_code} 无资产负债表数据")
                return []

            data_list = []
            for _, row in df.iterrows():
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("股票简称", ""),
                    "report_date": str(row.get("报告日期", "")),
                    "report_type": str(row.get("报告类型", "")),
                    # 核心指标
                    "total_assets": self._safe_float(row.get("资产总计")),
                    "total_liabilities": self._safe_float(row.get("负债合计")),
                    "owner_equity": self._safe_float(row.get("所有者权益合计")),
                }

                # 完整数据
                extra_data = {}
                for col in df.columns:
                    if col not in ["股票简称", "报告日期", "报告类型"]:
                        extra_data[col] = row.get(col)
                item["extra_data"] = extra_data

                data_list.append(item)

            logger.info(f"股票 {stock_code} 下载资产负债表 {len(data_list)} 条记录")
            return data_list

        except Exception as e:
            logger.error(f"下载 {stock_code} 资产负债表失败: {e}")
            return []
```

**Step 4: 添加现金流量表下载方法**

Add to `FinancialReportService` class:

```python
    def fetch_cash_flow_sheet(self, stock_code: str) -> List[Dict]:
        """
        下载现金流量表数据

        Args:
            stock_code: 股票代码

        Returns:
            现金流量表数据列表
        """
        try:
            symbol = self._code_format(stock_code)
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)

            if df.empty:
                logger.warning(f"股票 {stock_code} 无现金流量表数据")
                return []

            data_list = []
            for _, row in df.iterrows():
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("股票简称", ""),
                    "report_date": str(row.get("报告日期", "")),
                    "report_type": str(row.get("报告类型", "")),
                    # 核心指标
                    "operating_cash_flow": self._safe_float(row.get("经营活动产生的现金流量净额")),
                    "investing_cash_flow": self._safe_float(row.get("投资活动产生的现金流量净额")),
                    "financing_cash_flow": self._safe_float(row.get("筹资活动产生的现金流量净额")),
                }

                # 完整数据
                extra_data = {}
                for col in df.columns:
                    if col not in ["股票简称", "报告日期", "报告类型"]:
                        extra_data[col] = row.get(col)
                item["extra_data"] = extra_data

                data_list.append(item)

            logger.info(f"股票 {stock_code} 下载现金流量表 {len(data_list)} 条记录")
            return data_list

        except Exception as e:
            logger.error(f"下载 {stock_code} 现金流量表失败: {e}")
            return []
```

**Step 5: 更新 services/__init__.py**

Add to `src/ecox/services/__init__.py`:

```python
from .financial_report_service import FinancialReportService

__all__ = [
    "StockService",
    "PriceService",
    "ValuationService",
    "DataCollectionService",
    "DailyUpdateService",
    "AlertService",
    "FinancialReportService",  # 新增
]
```

**Step 6: 验证导入**

Run: `uv run python -c "from ecox.services import FinancialReportService; print('FinancialReportService imported successfully')"`

Expected: `FinancialReportService imported successfully`

**Step 7: Commit**

```bash
git add src/ecox/services/
git commit -m "feat: 添加 FinancialReportService 基础类

- 实现利润表下载方法
- 实现资产负债表下载方法
- 实现现金流量表下载方法
- 支持 JSON 存储完整数据"
```

---

## Task 5: 添加数据保存和验证逻辑

**Files:**
- Modify: `src/ecox/services/financial_report_service.py`

**Step 1: 添加利润表保存方法**

Add to `FinancialReportService` class:

```python
    def save_profit_sheet(self, stock_code: str, data_list: List[Dict]) -> Dict[str, int]:
        """
        保存利润表数据（带验证）

        Args:
            stock_code: 股票代码
            data_list: 利润表数据列表

        Returns:
            保存结果统计
        """
        saved_count = 0
        skipped_count = 0
        failed_count = 0

        with get_db_session() as session:
            for data in data_list:
                try:
                    # 验证数据
                    result = self.validator.validate_profit_sheet(data)

                    if not result.is_valid:
                        # 记录告警
                        self.alert_service.create_alert(
                            stock_code=stock_code,
                            stock_name=data.get("stock_name"),
                            alert_type="profit_sheet_validation_failed",
                            result=result,
                            raw_data=data,
                        )
                        failed_count += 1
                        logger.warning(f"{stock_code} {data.get('report_date')}: 利润表验证失败 - {result.errors}")
                        continue

                    # 检查是否已存在
                    existing = session.query(models.StockProfitSheet).filter(
                        models.StockProfitSheet.stock_code == stock_code,
                        models.StockProfitSheet.report_date == data.get("report_date")
                    ).first()

                    if existing:
                        # 更新
                        existing.total_revenue = data.get("total_revenue")
                        existing.operating_profit = data.get("operating_profit")
                        existing.net_profit = data.get("net_profit")
                        existing.basic_eps = data.get("basic_eps")
                        existing.extra_data = data.get("extra_data")
                        existing.update_time = datetime.now()
                        skipped_count += 1
                    else:
                        # 新增
                        record = models.StockProfitSheet(
                            stock_code=stock_code,
                            stock_name=data.get("stock_name", ""),
                            report_date=data.get("report_date"),
                            report_type=data.get("report_type"),
                            total_revenue=data.get("total_revenue"),
                            operating_profit=data.get("operating_profit"),
                            net_profit=data.get("net_profit"),
                            basic_eps=data.get("basic_eps"),
                            extra_data=data.get("extra_data"),
                        )
                        session.add(record)
                        saved_count += 1

                except Exception as e:
                    logger.error(f"保存 {stock_code} 利润表数据失败: {e}")
                    failed_count += 1

            session.commit()

        return {
            "saved": saved_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total": len(data_list),
        }
```

**Step 2: 添加资产负债表和现金流量表保存方法**

Similarly add `save_balance_sheet()` and `save_cash_flow_sheet()` methods following the same pattern.

**Step 3: 添加请求间隔配置**

Add to `src/ecox/config.py`:

```python
class FinancialReportConfig:
    """财报下载配置"""

    # API 调用间隔（秒）
    REQUEST_INTERVAL = 1.0

    # 批量大小
    BATCH_SIZE = 50


class Config:
    """基础配置类"""

    # ... 现有配置 ...

    # 财报配置
    financial_report = FinancialReportConfig()
```

**Step 4: 更新服务使用配置**

Modify `FinancialReportService` to use `Config.financial_report.REQUEST_INTERVAL` for delays between API calls.

**Step 5: Commit**

```bash
git add src/ecox/services/ src/ecox/config.py
git commit -m "feat: 添加财报数据保存和验证逻辑

- 实现带验证的保存方法
- 自动记录验证失败告警
- 支持数据去重和更新
- 添加配置参数"
```

---

## Task 6: 添加批量下载方法

**Files:**
- Modify: `src/ecox/services/financial_report_service.py`

**Step 1: 添加单股票全部报表下载**

Add to `FinancialReportService` class:

```python
    def fetch_all_reports(self, stock_code: str) -> Dict[str, List[Dict]]:
        """
        下载单股票的所有报表

        Args:
            stock_code: 股票代码

        Returns:
            各报表数据字典
        """
        logger.info(f"开始下载 {stock_code} 的所有财报")

        result = {
            "profit": [],
            "balance": [],
            "cash_flow": [],
        }

        # 下载利润表
        profit_data = self.fetch_profit_sheet(stock_code)
        if profit_data:
            save_result = self.save_profit_sheet(stock_code, profit_data)
            logger.info(f"利润表保存: {save_result}")
            result["profit"] = profit_data
        time.sleep(Config.financial_report.REQUEST_INTERVAL)

        # 下载资产负债表
        balance_data = self.fetch_balance_sheet(stock_code)
        if balance_data:
            save_result = self.save_balance_sheet(stock_code, balance_data)
            logger.info(f"资产负债表保存: {save_result}")
            result["balance"] = balance_data
        time.sleep(Config.financial_report.REQUEST_INTERVAL)

        # 下载现金流量表
        cash_flow_data = self.fetch_cash_flow_sheet(stock_code)
        if cash_flow_data:
            save_result = self.save_cash_flow_sheet(stock_code, cash_flow_data)
            logger.info(f"现金流量表保存: {save_result}")
            result["cash_flow"] = cash_flow_data

        return result
```

**Step 2: 添加批量下载方法**

Add to `FinancialReportService` class:

```python
    def batch_fetch_all_stocks(
        self,
        stock_codes: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        批量下载所有股票的财报

        Args:
            stock_codes: 股票代码列表，为空则获取所有股票
            limit: 最多下载数量

        Returns:
            统计结果
        """
        if not stock_codes:
            stock_codes = self._get_stock_list()

        if limit:
            stock_codes = stock_codes[:limit]

        logger.info(f"开始批量下载 {len(stock_codes)} 只股票的财报")

        total_profit = 0
        total_balance = 0
        total_cash_flow = 0
        failed = []

        for i, code in enumerate(stock_codes):
            try:
                logger.info(f"处理 {i+1}/{len(stock_codes)}: {code}")

                result = self.fetch_all_reports(code)

                total_profit += len(result.get("profit", []))
                total_balance += len(result.get("balance", []))
                total_cash_flow += len(result.get("cash_flow", []))

                # 打印进度
                if (i + 1) % 50 == 0:
                    logger.info(
                        f"进度: {i+1}/{len(stock_codes)}, "
                        f"利润表: {total_profit}, "
                        f"资产负债表: {total_balance}, "
                        f"现金流量表: {total_cash_flow}"
                    )

            except Exception as e:
                logger.error(f"处理 {code} 时出错: {e}")
                failed.append(code)

        logger.info("=" * 60)
        logger.info("批量下载完成!")
        logger.info(
            f"总计: 利润表 {total_profit} 条, "
            f"资产负债表 {total_balance} 条, "
            f"现金流量表 {total_cash_flow} 条"
        )
        if failed:
            logger.info(f"失败股票（前20个）: {failed[:20]}")

        return {
            "profit_count": total_profit,
            "balance_count": total_balance,
            "cash_flow_count": total_cash_flow,
            "failed_count": len(failed),
        }
```

**Step 3: 添加导入**

Add at the top of `financial_report_service.py`:

```python
from ..config import Config
from datetime import datetime
```

**Step 4: Commit**

```bash
git add src/ecox/services/financial_report_service.py
git commit -m "feat: 添加批量下载方法

- 添加单股票全部报表下载
- 添加批量下载方法
- 支持进度打印"
```

---

## Task 7: 添加单元测试

**Files:**
- Create: `tests/services/test_financial_report_service.py`

**Step 1: 编写测试用例**

Create `tests/services/test_financial_report_service.py`:

```python
"""财报下载服务测试"""
import pytest
from unittest.mock import Mock, patch
from ecox.services.financial_report_service import FinancialReportService


class TestFinancialReportService:
    """财报下载服务测试"""

    def test_code_format_sh(self):
        """测试上海股票代码格式化"""
        service = FinancialReportService()
        assert service._code_format("600809") == "SH600809"
        assert service._code_format("SH600809") == "SH600809"

    def test_code_format_sz(self):
        """测试深圳股票代码格式化"""
        service = FinancialReportService()
        assert service._code_format("000001") == "SZ000001"
        assert service._code_format("SZ000001") == "SZ000001"

    def test_safe_float(self):
        """测试安全浮点转换"""
        assert FinancialReportService._safe_float(123) == 123.0
        assert FinancialReportService._safe_float("123.45") == 123.45
        assert FinancialReportService._safe_float(None) is None
        assert FinancialReportService._safe_float("N/A") is None

    @patch('ecox.services.financial_report_service.ak.stock_profit_sheet_by_report_em')
    def test_fetch_profit_sheet_empty(self, mock_ak):
        """测试空数据处理"""
        import pandas as pd
        mock_ak.return_value = pd.DataFrame()

        service = FinancialReportService()
        result = service.fetch_profit_sheet("600809")

        assert result == []
```

**Step 2: 运行测试**

Run: `uv run pytest tests/services/test_financial_report_service.py -v`

Expected: 所有测试通过

**Step 3: Commit**

```bash
git add tests/services/
git commit -m "test: 添加财报下载服务单元测试"
```

---

## Task 8: 创建命令行入口脚本

**Files:**
- Create: `fetch_reports.py`

**Step 1: 创建命令行脚本**

Create `fetch_reports.py` in project root:

```python
#!/usr/bin/env python3
"""
财务报表下载脚本
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ecox.services.financial_report_service import FinancialReportService
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="财务报表下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载单只股票的所有财报
  python fetch_reports.py --stock 600809

  # 批量下载前 100 只股票
  python fetch_reports.py --batch --limit 100

  # 下载所有股票
  python fetch_reports.py --batch
        """
    )

    parser.add_argument("--stock", help="股票代码")
    parser.add_argument("--batch", action="store_true", help="批量下载")
    parser.add_argument("--limit", type=int, help="最多下载数量")

    args = parser.parse_args()
    service = FinancialReportService()

    if args.stock:
        # 单股票下载
        result = service.fetch_all_reports(args.stock)
        print(f"下载完成: 利润表 {len(result['profit'])} 条, "
              f"资产负债表 {len(result['balance'])} 条, "
              f"现金流量表 {len(result['cash_flow'])} 条")

    elif args.batch:
        # 批量下载
        result = service.batch_fetch_all_stocks(limit=args.limit)
        print(f"批量下载完成: {result}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Step 2: 测试脚本**

Run: `uv run python fetch_reports.py --help`

Expected: 显示帮助信息

**Step 3: Commit**

```bash
git add fetch_reports.py
git commit -m "feat: 添加财报下载命令行脚本

- 支持单股票下载
- 支持批量下载
- 支持数量限制"
```

---

## Task 9: 更新文档

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 更新 CLAUDE.md**

Add to the services section:

```markdown
### 财报下载模块

- **fetch_reports.py** - 财报下载命令行工具
  - 支持单股票下载
  - 支持批量下载所有股票

- **src/ecox/services/financial_report_service.py** - 财报下载服务
  - `fetch_profit_sheet()` - 下载利润表
  - `fetch_balance_sheet()` - 下载资产负债表
  - `fetch_cash_flow_sheet()` - 下载现金流量表
  - `batch_fetch_all_stocks()` - 批量下载
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: 更新 CLAUDE.md 添加财报模块说明"
```

---

## Task 10: 最终测试和收尾

**Step 1: 运行所有测试**

Run: `uv run pytest -v`

Expected: 所有测试通过

**Step 2: 运行 linting**

Run: `uv run ruff check src/ecox/services/financial_report_service.py src/ecox/validators/report_validator.py`

Expected: 无 linting 错误

**Step 3: 最终提交**

```bash
git add .
git commit -m "feat: 完成三大报表下载服务

✅ 功能完成:
- 扩展三大报表模型（JSON 字段）
- 实现 FinancialReportService
- 实现 ReportValidator
- 支持批量下载
- 支持数据验证

✅ 测试覆盖:
- 单元测试
- 命令行脚本

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```
