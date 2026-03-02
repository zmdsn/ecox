# 数据验证与清洗模块实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 在数据下载时实时验证和清洗股票数据，确保入库数据质量

**架构:** 创建独立的 `validators` 模块，包含价格/成交量/缺失数据验证器，集成到 DailyUpdateService 中

**技术栈:** Python 3.13, SQLAlchemy, pytest, dataclasses

---

## Task 1: 创建验证器模块目录结构

**Files:**
- Create: `src/ecox/validators/__init__.py`
- Create: `src/ecox/validators/result.py`
- Create: `src/ecox/validators/base.py`

**Step 1: 创建 validators 包的 `__init__.py`**

```python
# src/ecox/validators/__init__.py
"""
数据验证器模块
提供数据验证和清洗功能
"""

from .result import ValidationResult
from .base import DataValidator

__all__ = ["ValidationResult", "DataValidator"]
```

**Step 2: 创建 `result.py` 定义 ValidationResult 数据类**

```python
# src/ecox/validators/result.py
"""验证结果数据类"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class ValidationResult:
    """数据验证结果"""

    is_valid: bool
    """是否验证通过"""

    errors: List[str] = field(default_factory=list)
    """错误列表（致命问题，数据不可用）"""

    warnings: List[str] = field(default_factory=list)
    """警告列表（可修复的异常）"""

    cleaned_data: Optional[Dict[str, Any]] = None
    """清洗后的数据，如果数据可修复"""

    alert_level: str = "INFO"
    """告警级别: INFO, WARNING, ERROR"""

    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
        self.alert_level = "ERROR"

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
        if self.alert_level != "ERROR":
            self.alert_level = "WARNING"

    def has_issues(self) -> bool:
        """是否有任何问题"""
        return bool(self.errors or self.warnings)
```

**Step 3: 创建 `base.py` 定义验证器基类**

```python
# src/ecox/validators/base.py
"""验证器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from .result import ValidationResult


class DataValidator(ABC):
    """数据验证器基类"""

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证单条数据

        Args:
            data: 待验证的数据字典

        Returns:
            ValidationResult: 验证结果
        """
        pass

    def validate_batch(self, data_list: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        批量验证数据

        Args:
            data_list: 待验证的数据列表

        Returns:
            List[ValidationResult]: 验证结果列表
        """
        return [self.validate(data) for data in data_list]

    def _get_float(self, data: Dict, key: str, default: float = 0.0) -> float:
        """安全获取浮点数"""
        value = data.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
```

**Step 4: 验证代码语法**

Run: `python -c "from src.ecox.validators import ValidationResult, DataValidator; print('Import successful')"`

Expected: `Import successful`

**Step 5: 运行测试确保基础结构正常**

Run: `uv run pytest -v`

Expected: 所有现有测试通过

**Step 6: Commit**

```bash
git add src/ecox/validators/
git commit -m "feat: 创建验证器模块基础结构

- 添加 ValidationResult 数据类
- 添加 DataValidator 基类
- 创建 validators 包目录"
```

---

## Task 2: 实现 PriceValidator 价格验证器

**Files:**
- Create: `src/ecox/validators/price_validator.py`
- Create: `tests/validators/test_price_validator.py`
- Modify: `src/ecox/validators/__init__.py`

**Step 1: 编写 PriceValidator 的测试用例**

```python
# tests/validators/test_price_validator.py
"""价格验证器测试"""
import pytest
from datetime import date

from ecox.validators.price_validator import PriceValidator


class TestPriceValidator:
    """价格验证器测试"""

    def test_valid_price_data(self):
        """测试正常价格数据"""
        validator = PriceValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.8,
            "volume": 1000000,
        }
        result = validator.validate(data)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_negative_price(self):
        """测试价格为负"""
        validator = PriceValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": -1.0,
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.8,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "negative" in result.errors[0].lower()

    def test_zero_price(self):
        """测试价格为零（应产生警告）"""
        validator = PriceValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 0,
            "open_price": 0,
            "high_price": 0,
            "low_price": 0,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_ohlc_invalid_high_less_than_low(self):
        """测试 OHLC 逻辑错误：最高价 < 最低价"""
        validator = PriceValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "open_price": 10.0,
            "high_price": 9.0,
            "low_price": 10.0,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert any("ohlc" in err.lower() for err in result.errors)

    def test_ohlc_invalid_close_out_of_range(self):
        """测试 OHLC 逻辑错误：收盘价超出最高最低价范围"""
        validator = PriceValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 12.0,
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.0,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert any("ohlc" in err.lower() for err in result.errors)

    def test_price_out_of_range(self):
        """测试价格超出合理范围"""
        validator = PriceValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 20000,  # 超过最大值
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.0,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert any("range" in err.lower() for err in result.errors)
```

**Step 2: 运行测试验证失败**

Run: `uv run pytest tests/validators/test_price_validator.py -v`

Expected: `ImportError: cannot import name 'PriceValidator'`

**Step 3: 实现 PriceValidator**

```python
# src/ecox/validators/price_validator.py
"""价格验证器"""
from typing import Dict, Any
from datetime import date

from .base import DataValidator
from .result import ValidationResult


class PriceValidator(DataValidator):
    """价格验证器

    验证规则：
    1. 价格必须非负
    2. 价格在合理范围内 (0.01 - 10000)
    3. OHLC 逻辑关系正确
    4. 收盘价在 [最低价, 最高价] 范围内
    """

    # 价格范围配置
    MIN_PRICE = 0.01
    MAX_PRICE = 10000

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """验证价格数据"""
        result = ValidationResult(is_valid=True)

        # 获取价格字段
        close = self._get_float(data, "close_price")
        open_price = self._get_float(data, "open_price")
        high = self._get_float(data, "high_price")
        low = self._get_float(data, "low_price")

        # 检查价格是否为零（全部为零）
        if close == 0 and open_price == 0 and high == 0 and low == 0:
            result.add_error("所有价格字段为零，数据无效")
            return result

        # 检查价格为负
        if close < 0:
            result.add_error(f"收盘价为负: {close}")
        if open_price < 0:
            result.add_error(f"开盘价为负: {open_price}")
        if high < 0:
            result.add_error(f"最高价为负: {high}")
        if low < 0:
            result.add_error(f"最低价为负: {low}")

        # 检查价格范围
        if close > 0 and (close < self.MIN_PRICE or close > self.MAX_PRICE):
            result.add_error(f"收盘价超出合理范围: {close}")
        if open_price > 0 and (open_price < self.MIN_PRICE or open_price > self.MAX_PRICE):
            result.add_error(f"开盘价超出合理范围: {open_price}")

        # 检查 OHLC 逻辑关系
        if high > 0 and low > 0:
            if high < low:
                result.add_error(f"OHLC 逻辑错误: 最高价({high}) < 最低价({low})")

            # 检查收盘价是否在范围内
            if close > 0:
                if close < low or close > high:
                    result.add_error(
                        f"OHLC 逻辑错误: 收盘价({close}) 不在 [最低价({low}), 最高价({high})] 范围内"
                    )

            # 检查开盘价是否在范围内
            if open_price > 0:
                if open_price < low or open_price > high:
                    result.add_error(
                        f"OHLC 逻辑错误: 开盘价({open_price}) 不在 [最低价({low}), 最高价({high})] 范围内"
                    )

        return result
```

**Step 4: 更新 `__init__.py` 导出**

```python
# src/ecox/validators/__init__.py
"""
数据验证器模块
提供数据验证和清洗功能
"""

from .result import ValidationResult
from .base import DataValidator
from .price_validator import PriceValidator

__all__ = ["ValidationResult", "DataValidator", "PriceValidator"]
```

**Step 5: 运行测试验证通过**

Run: `uv run pytest tests/validators/test_price_validator.py -v`

Expected: 所有测试通过

**Step 6: Commit**

```bash
git add src/ecox/validators/ tests/validators/
git commit -m "feat: 实现 PriceValidator 价格验证器

- 验证价格非负
- 验证价格在合理范围内
- 验证 OHLC 逻辑关系
- 添加完整单元测试"
```

---

## Task 3: 实现 VolumeValidator 成交量验证器

**Files:**
- Create: `src/ecox/validators/volume_validator.py`
- Create: `tests/validators/test_volume_validator.py`
- Modify: `src/ecox/validators/__init__.py`

**Step 1: 编写 VolumeValidator 的测试用例**

```python
# tests/validators/test_volume_validator.py
"""成交量验证器测试"""
import pytest
from datetime import date

from ecox.validators.volume_validator import VolumeValidator


class TestVolumeValidator:
    """成交量验证器测试"""

    def test_valid_volume_data(self):
        """测试正常成交量数据"""
        validator = VolumeValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "volume": 1000000,
            "amount": 10500000,
        }
        result = validator.validate(data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_negative_volume(self):
        """测试成交量为负"""
        validator = VolumeValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "volume": -1000,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "negative" in result.errors[0].lower()

    def test_negative_amount(self):
        """测试成交额为负"""
        validator = VolumeValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "volume": 1000000,
            "amount": -1000,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_volume_amount_mismatch(self):
        """测试成交额与成交量不匹配（成交额过低）"""
        validator = VolumeValidator()
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "volume": 1000000,
            "amount": 1000,  # 远小于应该的金额
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert any("mismatch" in err.lower() for err in result.errors)
```

**Step 2: 运行测试验证失败**

Run: `uv run pytest tests/validators/test_volume_validator.py -v`

Expected: `ImportError: cannot import name 'VolumeValidator'`

**Step 3: 实现 VolumeValidator**

```python
# src/ecox/validators/volume_validator.py
"""成交量验证器"""
from typing import Dict, Any
from datetime import date

from .base import DataValidator
from .result import ValidationResult


class VolumeValidator(DataValidator):
    """成交量验证器

    验证规则：
    1. 成交量必须非负
    2. 成交额必须非负
    3. 成交额应该 >= 成交量 * 最低价（粗略检查）
    """

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """验证成交量数据"""
        result = ValidationResult(is_valid=True)

        # 获取成交量相关字段
        volume = data.get("volume")
        amount = data.get("amount")
        close = self._get_float(data, "close_price")
        low = self._get_float(data, "low_price", close)

        # 检查成交量
        if volume is not None:
            try:
                volume = int(volume)
                if volume < 0:
                    result.add_error(f"成交量为负: {volume}")
            except (ValueError, TypeError):
                result.add_error(f"成交量格式错误: {volume}")

        # 检查成交额
        if amount is not None:
            try:
                amount = float(amount)
                if amount < 0:
                    result.add_error(f"成交额为负: {amount}")

                # 检查成交额与成交量的合理性
                if volume and amount > 0 and close > 0:
                    # 粗略检查：成交额应该接近 成交量 * 价格
                    # 允许 10% 的误差范围（可能有复权等因素）
                    estimated_amount = volume * close
                    if amount < estimated_amount * 0.1:
                        result.add_error(
                            f"成交额与成交量不匹配: 成交额={amount}, "
                            f"预估={estimated_amount:.2f}"
                        )
            except (ValueError, TypeError):
                result.add_error(f"成交额格式错误: {amount}")

        return result
```

**Step 4: 更新 `__init__.py` 导出**

```python
# src/ecox/validators/__init__.py
"""
数据验证器模块
提供数据验证和清洗功能
"""

from .result import ValidationResult
from .base import DataValidator
from .price_validator import PriceValidator
from .volume_validator import VolumeValidator

__all__ = ["ValidationResult", "DataValidator", "PriceValidator", "VolumeValidator"]
```

**Step 5: 运行测试验证通过**

Run: `uv run pytest tests/validators/test_volume_validator.py -v`

Expected: 所有测试通过

**Step 6: Commit**

```bash
git add src/ecox/validators/ tests/validators/
git commit -m "feat: 实现 VolumeValidator 成交量验证器

- 验证成交量非负
- 验证成交额非负
- 检查成交额与成交量匹配性
- 添加完整单元测试"
```

---

## Task 4: 实现 CompositeValidator 组合验证器

**Files:**
- Create: `src/ecox/validators/composite.py`
- Create: `tests/validators/test_composite_validator.py`
- Modify: `src/ecox/validators/__init__.py`

**Step 1: 编写 CompositeValidator 的测试用例**

```python
# tests/validators/test_composite_validator.py
"""组合验证器测试"""
import pytest
from datetime import date

from ecox.validators.composite import CompositeValidator
from ecox.validators.price_validator import PriceValidator
from ecox.validators.volume_validator import VolumeValidator


class TestCompositeValidator:
    """组合验证器测试"""

    def test_valid_data(self):
        """测试正常数据通过所有验证器"""
        validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
        ])
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.8,
            "volume": 1000000,
            "amount": 10500000,
        }
        result = validator.validate(data)

        assert result.is_valid is True

    def test_invalid_price(self):
        """测试价格错误被检测"""
        validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
        ])
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": -1.0,  # 错误
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.8,
            "volume": 1000000,
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_invalid_volume(self):
        """测试成交量错误被检测"""
        validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
        ])
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": 10.5,
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.8,
            "volume": -1000,  # 错误
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_multiple_errors(self):
        """测试多个错误被收集"""
        validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
        ])
        data = {
            "stock_code": "600809",
            "trade_date": date(2026, 1, 10),
            "close_price": -1.0,  # 错误
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.0,  # 错误（high < low 不成立，但 close 为负）
            "volume": -1000,  # 错误
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) >= 2  # 至少有价格和成交量错误
```

**Step 2: 运行测试验证失败**

Run: `uv run pytest tests/validators/test_composite_validator.py -v`

Expected: `ImportError: cannot import name 'CompositeValidator'`

**Step 3: 实现 CompositeValidator**

```python
# src/ecox/validators/composite.py
"""组合验证器"""
from typing import List, Dict, Any

from .base import DataValidator
from .result import ValidationResult


class CompositeValidator(DataValidator):
    """组合验证器

    按顺序执行多个验证器，收集所有错误和警告
    """

    def __init__(self, validators: List[DataValidator]):
        """
        初始化组合验证器

        Args:
            validators: 验证器列表
        """
        self.validators = validators

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        执行所有验证器

        Args:
            data: 待验证的数据

        Returns:
            ValidationResult: 合并后的验证结果
        """
        combined_result = ValidationResult(is_valid=True)

        for validator in self.validators:
            result = validator.validate(data)

            # 合并错误
            for error in result.errors:
                combined_result.add_error(error)

            # 合并警告
            for warning in result.warnings:
                combined_result.add_warning(warning)

            # 如果有清洗后的数据，使用它
            if result.cleaned_data is not None:
                combined_result.cleaned_data = result.cleaned_data

        return result

    def add_validator(self, validator: DataValidator):
        """添加验证器"""
        self.validators.append(validator)
```

**Step 4: 更新 `__init__.py` 导出**

```python
# src/ecox/validators/__init__.py
"""
数据验证器模块
提供数据验证和清洗功能
"""

from .result import ValidationResult
from .base import DataValidator
from .price_validator import PriceValidator
from .volume_validator import VolumeValidator
from .composite import CompositeValidator

__all__ = [
    "ValidationResult",
    "DataValidator",
    "PriceValidator",
    "VolumeValidator",
    "CompositeValidator",
]
```

**Step 5: 运行测试验证通过**

Run: `uv run pytest tests/validators/test_composite_validator.py -v`

Expected: 所有测试通过

**Step 6: Commit**

```bash
git add src/ecox/validators/ tests/validators/
git commit -m "feat: 实现 CompositeValidator 组合验证器

- 支持组合多个验证器
- 收集所有错误和警告
- 添加完整单元测试"
```

---

## Task 5: 创建 DataAlert 模型

**Files:**
- Modify: `src/ecox/models/__init__.py`
- Create: `src/ecox/alembic/versions/xxxx_add_data_alerts_table.py`

**Step 1: 在 models 中添加 DataAlert 模型**

```python
# 在 src/ecox/models/__init__.py 末尾添加

class DataAlert(Base):
    """数据告警记录表"""

    __tablename__ = "data_alerts"

    id = Column(Integer, primary_key=True)
    alert_level = Column(String(10), nullable=False, index=True)  # ERROR/WARNING/INFO
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    alert_type = Column(String(50), nullable=False, index=True)  # price_invalid/volume_zero/...
    alert_message = Column(Text, nullable=False)
    raw_data = Column(JSON)  # 原始数据
    trade_date = Column(Date, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)

    def __repr__(self):
        return f"<DataAlert({self.alert_level} {self.stock_code} {self.alert_type})>"


# 更新 __all__ 导出
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
    "DataAlert",  # 新增
]
```

**Step 2: 创建 Alembic 迁移脚本**

```bash
# 生成迁移脚本
uv run alembic revision -m "add data alerts table"
```

编辑生成的迁移文件：

```python
# src/ecox/alembic/versions/xxxx_add_data_alerts_table.py
"""add data alerts table

Revision ID: xxxx
Revises: （上一个版本的ID）
Create Date: 2026-03-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = '（上一个版本的ID）'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'data_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_level', sa.String(length=10), nullable=False),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('stock_name', sa.String(length=100), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('raw_data', JSON(), nullable=True),
        sa.Column('trade_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_alerts_alert_level'), 'data_alerts', ['alert_level'], unique=False)
    op.create_index(op.f('ix_data_alerts_alert_type'), 'data_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_data_alerts_stock_code'), 'data_alerts', ['stock_code'], unique=False)
    op.create_index(op.f('ix_data_alerts_trade_date'), 'data_alerts', ['trade_date'], unique=False)
    op.create_index(op.f('ix_data_alerts_created_at'), 'data_alerts', ['created_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_data_alerts_created_at'), table_name='data_alerts')
    op.drop_index(op.f('ix_data_alerts_trade_date'), table_name='data_alerts')
    op.drop_index(op.f('ix_data_alerts_stock_code'), table_name='data_alerts')
    op.drop_index(op.f('ix_data_alerts_alert_type'), table_name='data_alerts')
    op.drop_index(op.f('ix_data_alerts_alert_level'), table_name='data_alerts')
    op.drop_table('data_alerts')
```

**Step 3: 运行迁移**

Run: `uv run alembic upgrade head`

Expected: `Running upgrade... OK`

**Step 4: 验证表创建**

Run: `uv run python -c "from ecox.models import DataAlert; print('DataAlert model imported successfully')"`

Expected: `DataAlert model imported successfully`

**Step 5: Commit**

```bash
git add src/ecox/models/__init__.py src/ecox/alembic/versions/
git commit -m "feat: 添加 DataAlert 告警记录表

- 记录数据验证告警信息
- 支持多种告警级别和类型
- 添加数据库迁移脚本"
```

---

## Task 6: 创建 AlertService 告警服务

**Files:**
- Create: `src/ecox/services/alert_service.py`
- Modify: `src/ecox/services/__init__.py`

**Step 1: 创建 AlertService**

```python
# src/ecox/validators/alert_service.py
"""告警服务"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db_session
from ..models import DataAlert
from .result import ValidationResult


class AlertService:
    """告警服务"""

    def __init__(self):
        pass

    def create_alert(
        self,
        stock_code: str,
        stock_name: Optional[str],
        alert_type: str,
        result: ValidationResult,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> DataAlert:
        """
        创建告警记录

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            alert_type: 告警类型
            result: 验证结果
            raw_data: 原始数据

        Returns:
            DataAlert: 创建的告警记录
        """
        # 构建告警消息
        messages = result.errors if result.errors else result.warnings
        alert_message = "; ".join(messages)

        # 获取交易日期
        trade_date = None
        if raw_data and "trade_date" in raw_data:
            trade_date = raw_data["trade_date"]

        alert = DataAlert(
            alert_level=result.alert_level,
            stock_code=stock_code,
            stock_name=stock_name,
            alert_type=alert_type,
            alert_message=alert_message,
            raw_data=raw_data,
            trade_date=trade_date,
            created_at=datetime.now(),
        )

        with get_db_session() as session:
            session.add(alert)
            session.commit()
            session.refresh(alert)

        return alert

    def create_alerts_batch(
        self,
        alerts: List[Dict[str, Any]]
    ) -> int:
        """
        批量创建告警记录

        Args:
            alerts: 告警数据列表，每个元素包含:
                - stock_code: 股票代码
                - stock_name: 股票名称
                - alert_type: 告警类型
                - result: ValidationResult
                - raw_data: 原始数据

        Returns:
            int: 创建的告警数量
        """
        with get_db_session() as session:
            count = 0
            for alert_data in alerts:
                messages = alert_data["result"].errors or alert_data["result"].warnings
                alert_message = "; ".join(messages)

                raw_data = alert_data.get("raw_data")
                trade_date = None
                if raw_data and "trade_date" in raw_data:
                    trade_date = raw_data["trade_date"]

                alert = DataAlert(
                    alert_level=alert_data["result"].alert_level,
                    stock_code=alert_data["stock_code"],
                    stock_name=alert_data.get("stock_name"),
                    alert_type=alert_data["alert_type"],
                    alert_message=alert_message,
                    raw_data=raw_data,
                    trade_date=trade_date,
                    created_at=datetime.now(),
                )
                session.add(alert)
                count += 1

            session.commit()

        return count

    def get_unresolved_alerts(
        self,
        stock_code: Optional[str] = None,
        limit: int = 100,
    ) -> List[DataAlert]:
        """
        获取未解决的告警

        Args:
            stock_code: 股票代码过滤
            limit: 最多返回数量

        Returns:
            List[DataAlert]: 告警列表
        """
        with get_db_session() as session:
            query = session.query(DataAlert).filter(
                DataAlert.resolved == False
            )

            if stock_code:
                query = query.filter(DataAlert.stock_code == stock_code)

            alerts = query.order_by(
                DataAlert.created_at.desc()
            ).limit(limit).all()

            return alerts
```

**Step 2: 更新 services/__init__.py 导出**

```python
# src/ecox/services/__init__.py 添加
from ..validators.alert_service import AlertService

__all__ = [
    "StockService",
    "PriceService",
    "ValuationService",
    "DataCollectionService",
    "DailyUpdateService",
    "AlertService",  # 新增
]
```

**Step 3: 验证导入**

Run: `uv run python -c "from ecox.services import AlertService; print('AlertService imported successfully')"`

Expected: `AlertService imported successfully`

**Step 4: Commit**

```bash
git add src/ecox/validators/alert_service.py src/ecox/services/__init__.py
git commit -m "feat: 添加 AlertService 告警服务

- 支持单个和批量创建告警
- 支持查询未解决告警"
```

---

## Task 7: 集成验证器到 DailyUpdateService

**Files:**
- Modify: `src/ecox/services/daily_update_service.py`

**Step 1: 修改 DailyUpdateService 添加验证逻辑**

在 `save_price_data` 方法中添加验证：

```python
# 在文件开头添加导入
from ..validators import CompositeValidator, PriceValidator, VolumeValidator
from ..validators.alert_service import AlertService

# 修改 DailyUpdateService 类
class DailyUpdateService:
    """每日股票数据更新服务"""

    def __init__(self):
        self.stock_service = StockService()
        self.session = None
        # 新增：初始化验证器
        self.validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
        ])
        self.alert_service = AlertService()

    # 修改 save_price_data 方法
    def save_price_data(
        self,
        stock_code: str,
        data_list: List[Dict],
    ) -> Dict[str, int]:
        """
        保存价格数据到数据库（增量更新，带验证）

        只保存验证通过的数据，记录告警信息
        """
        with get_db_session() as session:
            saved_count = 0
            skipped_count = 0
            failed_count = 0

            # 获取已存在的日期
            existing_dates = set()
            existing = session.query(
                models.StockPrice.trade_date
            ).filter(
                models.StockPrice.stock_code == stock_code,
                models.StockPrice.trade_date.in_([d['trade_date'] for d in data_list])
            ).all()

            for e in existing:
                existing_dates.add(e.trade_date)

            # 获取最后一个价格用于计算涨跌幅
            last_price = session.query(
                models.StockPrice.close_price
            ).filter(
                models.StockPrice.stock_code == stock_code
            ).order_by(
                models.StockPrice.trade_date.desc()
            ).first()

            prev_close = float(last_price.close_price) if last_price else None

            # 新增：验证和告警收集
            alerts_to_create = []

            # 计算涨跌幅并验证
            sorted_data = sorted(data_list, key=lambda x: x['trade_date'])

            for item in sorted_data:
                # 跳过已存在的日期
                if item['trade_date'] in existing_dates:
                    skipped_count += 1
                    prev_close = item['close_price']
                    continue

                # 计算涨跌幅
                change_rate = None
                if prev_close is not None and prev_close > 0:
                    change_rate = ((item['close_price'] - prev_close) / prev_close) * 100

                # 添加 change_rate 到数据中
                item_with_change = item.copy()
                item_with_change['change_rate'] = change_rate

                # 新增：验证数据
                result = self.validator.validate(item_with_change)

                if not result.is_valid:
                    # 数据无效，记录告警
                    alerts_to_create.append({
                        "stock_code": stock_code,
                        "stock_name": item.get("stock_name"),  # 如果有的话
                        "alert_type": "data_validation_failed",
                        "result": result,
                        "raw_data": item_with_change,
                    })
                    failed_count += 1
                    logger.warning(f"{stock_code} {item['trade_date']}: 数据验证失败 - {result.errors}")
                    continue

                # 使用清洗后的数据或原始数据
                data_to_save = result.cleaned_data if result.cleaned_data else item_with_change

                price = models.StockPrice(
                    stock_code=stock_code,
                    trade_date=data_to_save['trade_date'],
                    close_price=data_to_save['close_price'],
                    open_price=data_to_save.get('open_price'),
                    high_price=data_to_save.get('high_price'),
                    low_price=data_to_save.get('low_price'),
                    volume=data_to_save.get('volume'),
                    amount=data_to_save.get('amount'),
                    change_rate=change_rate,
                )
                session.add(price)
                saved_count += 1

                prev_close = data_to_save['close_price']

            # 新增：批量创建告警
            if alerts_to_create:
                try:
                    self.alert_service.create_alerts_batch(alerts_to_create)
                except Exception as e:
                    logger.error(f"创建告警失败: {e}")

            session.commit()

            return {
                "saved": saved_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "total": len(data_list),
            }
```

**Step 2: 运行测试确保现有功能正常**

Run: `uv run pytest tests/ -v`

Expected: 所有现有测试通过

**Step 3: 手动测试验证功能**

Run: `uv run python -c "
from ecox.services.daily_update_service import DailyUpdateService
from datetime import date

service = DailyUpdateService()

# 测试验证器
test_data = {
    'stock_code': 'TEST001',
    'trade_date': date(2026, 3, 2),
    'close_price': -1.0,  # 无效价格
    'open_price': 10.0,
    'high_price': 11.0,
    'low_price': 9.0,
}

result = service.validator.validate(test_data)
print(f'验证结果: is_valid={result.is_valid}, errors={result.errors}')
print('验证器工作正常')
"`

Expected: `验证结果: is_valid=False, errors=['收盘价为负: -1.0']`

**Step 4: Commit**

```bash
git add src/ecox/services/daily_update_service.py
git commit -m "feat: 集成数据验证器到 DailyUpdateService

- 在保存数据前进行验证
- 拒绝无效数据入库
- 自动记录告警信息"
```

---

## Task 8: 添加配置参数

**Files:**
- Modify: `src/ecox/config.py`

**Step 1: 添加验证配置**

```python
# 在 src/ecox/config.py 中添加

class ValidationConfig:
    """验证配置"""

    # 价格范围
    MIN_PRICE = float(os.getenv("VALIDATION_MIN_PRICE", "0.01"))
    MAX_PRICE = float(os.getenv("VALIDATION_MAX_PRICE", "10000"))

    # 涨跌幅限制（普通股）
    MAX_CHANGE_RATE = float(os.getenv("VALIDATION_MAX_CHANGE_RATE", "20"))
    MAX_CHANGE_RATE_ST = float(os.getenv("VALIDATION_MAX_CHANGE_RATE_ST", "5"))

    # 成交量/成交额匹配阈值
    AMOUNT_VOLUME_RATIO_MIN = float(os.getenv("VALIDATION_AMOUNT_RATIO_MIN", "0.1"))

    # 是否启用严格模式（严格模式下 WARNING 也会拒绝入库）
    STRICT_MODE = os.getenv("VALIDATION_STRICT_MODE", "false").lower() == "true"


# 将配置添加到 Config 类
class Config:
    """基础配置类"""

    # ... 现有配置 ...

    # 验证配置
    validation = ValidationConfig()
```

**Step 2: 验证配置加载**

Run: `uv run python -c "from ecox.config import Config; print(f'MIN_PRICE={Config.validation.MIN_PRICE}')"`

Expected: `MIN_PRICE=0.01`

**Step 3: Commit**

```bash
git add src/ecox/config.py
git commit -m "feat: 添加验证配置参数

- 价格范围配置
- 涨跌幅限制配置
- 严格模式开关"
```

---

## Task 9: 更新 validators 使用配置

**Files:**
- Modify: `src/ecox/validators/price_validator.py`
- Modify: `src/ecox/validators/volume_validator.py`

**Step 1: 修改 PriceValidator 使用配置**

```python
# 在 src/ecox/validators/price_validator.py 中添加配置导入

from ..config import Config

class PriceValidator(DataValidator):
    """价格验证器"""

    # 使用配置而非硬编码
    @property
    def MIN_PRICE(self):
        return Config.validation.MIN_PRICE

    @property
    def MAX_PRICE(self):
        return Config.validation.MAX_PRICE

    # ... 其余代码保持不变 ...
```

**Step 2: 修改 VolumeValidator 使用配置**

```python
# 在 src/ecox/validators/volume_validator.py 中添加配置导入

from ..config import Config

class VolumeValidator(DataValidator):
    """成交量验证器"""

    # 使用配置
    @property
    def AMOUNT_VOLUME_RATIO_MIN(self):
        return Config.validation.AMOUNT_VOLUME_RATIO_MIN

    # 在验证方法中使用 self.AMOUNT_VOLUME_RATIO_MIN 替代硬编码的 0.1
    if volume and amount > 0 and close > 0:
        estimated_amount = volume * close
        if amount < estimated_amount * self.AMOUNT_VOLUME_RATIO_MIN:
            result.add_error(...)
```

**Step 3: 运行测试确保一切正常**

Run: `uv run pytest tests/validators/ -v`

Expected: 所有测试通过

**Step 4: Commit**

```bash
git add src/ecox/validators/
git commit -m "refactor: 验证器使用配置参数

- 从 Config 读取验证参数
- 支持通过环境变量配置"
```

---

## Task 10: 添加集成测试

**Files:**
- Create: `tests/integration/test_validation_integration.py`

**Step 1: 创建集成测试**

```python
# tests/integration/test_validation_integration.py
"""验证模块集成测试"""
import pytest
from datetime import date

from ecox.services.daily_update_service import DailyUpdateService
from ecox.database import get_db_session
from ecox import models


class TestValidationIntegration:
    """验证模块集成测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return DailyUpdateService()

    @pytest.fixture
    def clean_db(self):
        """清理测试数据"""
        with get_db_session() as session:
            # 删除测试股票的数据
            session.query(models.StockPrice).filter(
                models.StockPrice.stock_code == "TEST001"
            ).delete()
            session.query(models.DataAlert).filter(
                models.DataAlert.stock_code == "TEST001"
            ).delete()
            session.commit()
        yield
        # 测试后清理
        with get_db_session() as session:
            session.query(models.StockPrice).filter(
                models.StockPrice.stock_code == "TEST001"
            ).delete()
            session.query(models.DataAlert).filter(
                models.DataAlert.stock_code == "TEST001"
            ).delete()
            session.commit()

    def test_valid_data_saved(self, service, clean_db):
        """测试有效数据被保存"""
        data_list = [
            {
                "stock_code": "TEST001",
                "trade_date": date(2026, 3, 1),
                "close_price": 10.5,
                "open_price": 10.0,
                "high_price": 11.0,
                "low_price": 9.8,
                "volume": 1000000,
                "amount": 10500000,
            }
        ]

        result = service.save_price_data("TEST001", data_list)

        assert result["saved"] == 1
        assert result["failed"] == 0

        # 验证数据已保存
        with get_db_session() as session:
            saved = session.query(models.StockPrice).filter(
                models.StockPrice.stock_code == "TEST001"
            ).first()
            assert saved is not None
            assert saved.close_price == 10.5

    def test_invalid_data_not_saved(self, service, clean_db):
        """测试无效数据不被保存"""
        data_list = [
            {
                "stock_code": "TEST001",
                "trade_date": date(2026, 3, 1),
                "close_price": -1.0,  # 无效
                "open_price": 10.0,
                "high_price": 11.0,
                "low_price": 9.0,
                "volume": 1000000,
            }
        ]

        result = service.save_price_data("TEST001", data_list)

        assert result["saved"] == 0
        assert result["failed"] == 1

        # 验证数据未保存
        with get_db_session() as session:
            saved = session.query(models.StockPrice).filter(
                models.StockPrice.stock_code == "TEST001"
            ).first()
            assert saved is None

        # 验证告警已记录
        with get_db_session() as session:
            alert = session.query(models.DataAlert).filter(
                models.DataAlert.stock_code == "TEST001"
            ).first()
            assert alert is not None
            assert alert.alert_level == "ERROR"

    def test_mixed_data_partial_save(self, service, clean_db):
        """测试混合数据（有效+无效）部分保存"""
        data_list = [
            {
                "stock_code": "TEST001",
                "trade_date": date(2026, 3, 1),
                "close_price": 10.5,  # 有效
                "open_price": 10.0,
                "high_price": 11.0,
                "low_price": 9.8,
                "volume": 1000000,
                "amount": 10500000,
            },
            {
                "stock_code": "TEST001",
                "trade_date": date(2026, 3, 2),
                "close_price": -1.0,  # 无效
                "open_price": 10.0,
                "high_price": 11.0,
                "low_price": 9.0,
                "volume": 1000000,
            },
        ]

        result = service.save_price_data("TEST001", data_list)

        assert result["saved"] == 1
        assert result["failed"] == 1

        # 验证只有有效数据被保存
        with get_db_session() as session:
            saved = session.query(models.StockPrice).filter(
                models.StockPrice.stock_code == "TEST001"
            ).all()
            assert len(saved) == 1
            assert saved[0].close_price == 10.5
```

**Step 2: 运行集成测试**

Run: `uv run pytest tests/integration/test_validation_integration.py -v`

Expected: 所有测试通过

**Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test: 添加验证模块集成测试

- 测试有效数据保存
- 测试无效数据拒绝
- 测试混合数据处理"
```

---

## Task 11: 更新 CLAUDE.md 文档

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 在 CLAUDE.md 中添加验证模块说明**

在 "代码架构" 部分后添加：

```
### 数据验证模块（src/ecox/validators/）

- **validators/base.py** - 验证器基类
  - DataValidator: 所有验证器的抽象基类
  - 提供单条和批量验证接口

- **validators/result.py** - 验证结果数据类
  - ValidationResult: 封装验证结果（错误/警告/清洗数据）

- **validators/price_validator.py** - 价格验证器
  - 检查价格非负、合理范围
  - 验证 OHLC 逻辑关系

- **validators/volume_validator.py** - 成交量验证器
  - 检查成交量/成交额非负
  - 验证成交额与成交量匹配性

- **validators/composite.py** - 组合验证器
  - 按顺序执行多个验证器
  - 收集所有错误和警告

- **validators/alert_service.py** - 告警服务
  - 创建告警记录
  - 查询未解决告警

### 告警记录表（data_alerts）

记录数据验证失败和异常信息：
- alert_level: 告警级别（ERROR/WARNING/INFO）
- stock_code: 股票代码
- alert_type: 告警类型（price_invalid/volume_zero/...）
- alert_message: 告警消息
- raw_data: 原始数据（JSON格式）
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: 更新 CLAUDE.md 添加验证模块说明"
```

---

## Task 12: 运行完整测试套件

**Step 1: 运行所有测试**

Run: `uv run pytest -v --cov=src/ecox/validators --cov-report=term-missing`

Expected: 所有测试通过，覆盖率 > 80%

**Step 2: 运行 linting 检查**

Run: `uv run ruff check src/ecox/validators/`

Expected: 无 linting 错误

**Step 3: 最终 Commit**

```bash
git add .
git commit -m "feat: 完成数据验证与清洗模块

✅ 功能完成:
- PriceValidator 价格验证器
- VolumeValidator 成交量验证器
- CompositeValidator 组合验证器
- AlertService 告警服务
- DataAlert 告警记录表
- 集成到 DailyUpdateService

✅ 测试覆盖:
- 单元测试
- 集成测试
- 测试覆盖率 > 80%

✅ 配置支持:
- 环境变量配置
- 严格模式开关"
```

---

## 执行说明

### 前置条件
- Python 3.13
- PostgreSQL 数据库运行中
- 数据库表已创建

### 执行顺序
按照 Task 1 到 Task 12 的顺序执行，每个 Task 完成后再执行下一个。

### 验证检查点
- Task 1-4: 验证器模块单元测试
- Task 5: 数据库迁移成功
- Task 7: DailyUpdateService 集成验证
- Task 10: 集成测试通过
- Task 12: 完整测试套件通过
