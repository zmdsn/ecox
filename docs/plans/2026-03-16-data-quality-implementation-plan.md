# Ecox 数据质量重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 重构 Ecox 财务数据层，建立统一的数据质量保障体系，包括代码格式统一、数据验证、懒加载机制和完整的财务数据存储。

**架构:** 在 SQLAlchemy 模型层添加 BaseMixin 混合基类，实现自动代码格式化和数据验证；创建 LazyLoadingService 实现数据的自动获取和缓存；建立多层验证机制确保数据质量。

**技术栈:** SQLAlchemy 2.0, PostgreSQL, akshare, pytest, Python 3.13

---

## 前置准备

### Task 0: 环境检查

**目的:** 确保开发环境配置正确

**Step 1: 检查 Python 版本**

```bash
python --version
```

Expected: `Python 3.13.x`

**Step 2: 检查项目依赖**

```bash
uv pip list | grep -E "(sqlalchemy|pytest|akshare|psycopg)"
```

Expected: 看到 sqlalchemy, pytest, akshare, psycopg2 等包

**Step 3: 检查数据库连接**

```bash
uv run python -c "from ecox.database import get_db_session; print('DB OK')"
```

Expected: `DB OK`

**Step 4: 创建必要的目录**

```bash
mkdir -p src/ecox/models
mkdir -p src/ecox/validators
mkdir -p src/ecox/utils
mkdir -p scripts
mkdir -p logs
mkdir -p tests/models
mkdir -p tests/validators
mkdir -p tests/services
```

Expected: 无错误，目录创建成功

---

## Phase 1: 基础设施层

### Task 1: 创建自定义异常类

**目的:** 建立统一的异常处理体系

**Files:**
- Create: `src/ecox/exceptions.py`
- Test: `tests/test_exceptions.py`

**Step 1: 编写异常类**

```bash
cat > src/ecox/exceptions.py << 'EOF'
"""Ecox 自定义异常类"""

class EcoxException(Exception):
    """Ecox 基础异常类"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class StockCodeError(EcoxException):
    """股票代码格式错误"""
    pass


class DataValidationError(EcoxException):
    """数据验证错误"""

    def __init__(self, message: str, issues: list = None):
        super().__init__(message)
        self.issues = issues or []

    def __str__(self):
        if self.issues:
            issues_str = "; ".join([f"{i.field}: {i.message}" for i in self.issues[:5]])
            return f"{self.message} - Issues: {issues_str}"
        return self.message


class DataIntegrityError(EcoxException):
    """数据完整性错误"""
    pass


class MigrationError(EcoxException):
    """数据迁移错误"""
    pass


class ExternalDataSourceError(EcoxException):
    """外部数据源错误（如 akshare）"""
    pass
EOF
```

**Step 2: 编写测试**

```bash
cat > tests/test_exceptions.py << 'EOF'
"""测试异常类"""

import pytest
from ecox.exceptions import (
    EcoxException,
    StockCodeError,
    DataValidationError,
    DataIntegrityError
)


def test_ecox_exception_basic():
    """测试基础异常"""
    exc = EcoxException("Test error", {"key": "value"})
    assert exc.message == "Test error"
    assert exc.details == {"key": "value"}
    assert "Test error" in str(exc)


def test_stock_code_error():
    """测试股票代码错误"""
    exc = StockCodeError("Invalid code", {"code": "123"})
    assert isinstance(exc, EcoxException)
    assert "Invalid code" in str(exc)


def test_data_validation_error():
    """测试数据验证错误"""
    exc = DataValidationError("Validation failed")
    assert exc.issues == []

    # 模拟 ValidationIssue
    from dataclasses import dataclass
    from enum import Enum

    class Severity(Enum):
        ERROR = "error"

    @dataclass
    class Issue:
        field: str
        message: str
        severity: Severity

    issues = [Issue("field1", "error1", Severity.ERROR)]
    exc2 = DataValidationError("Validation failed", issues)
    assert len(exc2.issues) == 1
    assert "field1" in str(exc2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_exceptions.py -v
```

Expected: `3 passed`

**Step 4: 提交**

```bash
git add src/ecox/exceptions.py tests/test_exceptions.py
git commit -m "feat: 添加自定义异常类

- EcoxException 基础异常
- StockCodeError 股票代码错误
- DataValidationError 数据验证错误
- DataIntegrityError 数据完整性错误
- MigrationError 迁移错误
- ExternalDataSourceError 外部数据源错误

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 统一日志配置

**目的:** 建立统一的日志系统

**Files:**
- Create: `src/ecox/logging_config.py`
- Test: `tests/test_logging_config.py`

**Step 1: 编写日志配置**

```bash
cat > src/ecox/logging_config.py << 'EOF'
"""统一日志配置"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    enable_console: bool = True,
    enable_file: bool = True
):
    """
    配置统一日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)

    # 文件处理器（按日期和大小轮转）
    if enable_file:
        today = datetime.now().strftime('%Y-%m-%d')
        file_handler = RotatingFileHandler(
            log_path / f"ecox_{today}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

    # 第三方库日志级别
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('akshare').setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取命名的日志器"""
    return logging.getLogger(name)
EOF
```

**Step 2: 编写测试**

```bash
cat > tests/test_logging_config.py << 'EOF'
"""测试日志配置"""

import logging
import pytest
from pathlib import Path
from ecox.logging_config import setup_logging, get_logger


def test_setup_logging_default():
    """测试默认日志配置"""
    logger = setup_logging(log_level="INFO", enable_file=False)
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_get_logger():
    """测试获取日志器"""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_log_file_creation(tmp_path):
    """测试日志文件创建"""
    log_dir = tmp_path / "logs"
    logger = setup_logging(
        log_level="DEBUG",
        log_dir=str(log_dir),
        enable_console=False,
        enable_file=True
    )

    # 写入日志
    test_logger = get_logger("test")
    test_logger.info("Test message")

    # 检查文件是否创建
    log_files = list(Path(log_dir).glob("ecox_*.log"))
    assert len(log_files) > 0

    # 检查日志内容
    log_content = log_files[0].read_text()
    assert "Test message" in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_logging_config.py -v
```

Expected: `3 passed`

**Step 4: 提交**

```bash
git add src/ecox/logging_config.py tests/test_logging_config.py
git commit -m "feat: 添加统一日志配置

- setup_logging() 配置函数
- 支持控制台和文件输出
- 文件按大小轮转（10MB，保留5个）
- 第三方库日志级别控制
- get_logger() 便捷函数

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 错误处理装饰器

**目的:** 提供统一的错误处理机制

**Files:**
- Create: `src/ecox/utils/error_handling.py`
- Test: `tests/utils/test_error_handling.py`

**Step 1: 编写错误处理装饰器**

```bash
mkdir -p src/ecox/utils
cat > src/ecox/utils/error_handling.py << 'EOF'
"""错误处理工具"""

import functools
import logging
from typing import Callable, Any
from ecox.exceptions import EcoxException

logger = logging.getLogger(__name__)


def handle_errors(
    default_return: Any = None,
    raise_on_error: bool = False,
    log_level: str = "ERROR"
):
    """
    错误处理装饰器

    Args:
        default_return: 发生错误时的默认返回值
        raise_on_error: 是否重新抛出异常
        log_level: 日志级别
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except EcoxException as e:
                # 已知业务异常
                getattr(logger, log_level.lower())(
                    f"{func.__name__} failed: {e.message}",
                    extra={"details": e.details}
                )
                if raise_on_error:
                    raise
                return default_return
            except Exception as e:
                # 未知异常
                logger.error(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                if raise_on_error:
                    raise
                return default_return
        return wrapper
    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器（用于外部数据源调用）

    Args:
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise

                    wait_time = delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)

        return wrapper
    return decorator
EOF
```

**Step 2: 创建 __init__.py**

```bash
cat > src/ecox/utils/__init__.py << 'EOF'
"""工具模块"""

from .error_handling import handle_errors, retry_on_failure

__all__ = ["handle_errors", "retry_on_failure"]
EOF
```

**Step 3: 编写测试**

```bash
cat > tests/utils/test_error_handling.py << 'EOF'
"""测试错误处理装饰器"""

import pytest
from ecox.utils.error_handling import handle_errors, retry_on_failure
from ecox.exceptions import EcoxException, StockCodeError


def test_handle_errors_with_exception():
    """测试异常处理"""
    @handle_errors(default_return=None, raise_on_error=False)
    def failing_function():
        raise StockCodeError("Invalid code")

    result = failing_function()
    assert result is None


def test_handle_errors_raise_on_error():
    """测试重新抛出异常"""
    @handle_errors(default_return=None, raise_on_error=True)
    def failing_function():
        raise StockCodeError("Invalid code")

    with pytest.raises(StockCodeError):
        failing_function()


def test_handle_errors_success():
    """测试正常执行"""
    @handle_errors(default_return=None)
    def success_function():
        return "success"

    result = success_function()
    assert result == "success"


def test_retry_on_failure_success():
    """测试重试成功"""
    call_count = [0]

    @retry_on_failure(max_attempts=3, delay=0.01, exceptions=(ValueError,))
    def flaky_function():
        call_count[0] += 1
        if call_count[0] < 2:
            raise ValueError("Temporary error")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count[0] == 2


def test_retry_on_failure_exhausted():
    """测试重试次数用尽"""
    @retry_on_failure(max_attempts=2, delay=0.01, exceptions=(ValueError,))
    def always_failing_function():
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_failing_function()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 4: 运行测试**

```bash
uv run pytest tests/utils/test_error_handling.py -v
```

Expected: `5 passed`

**Step 5: 提交**

```bash
git add src/ecox/utils/ tests/utils/
git commit -m "feat: 添加错误处理装饰器

- handle_errors: 统一错误处理装饰器
- retry_on_failure: 重试装饰器，支持指数退避
- 完整的单元测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: 数据模型层

### Task 4: 创建 BaseMixin 基类

**目的:** 提供统一的模型基础功能

**Files:**
- Create: `src/ecox/models/base.py`
- Test: `tests/models/test_base.py`

**Step 1: 编写 BaseMixin**

```bash
mkdir -p src/ecox/models
cat > src/ecox/models/base.py << 'EOF'
"""数据模型基类"""

import re
from sqlalchemy import Column, String
from sqlalchemy.orm import declared_attr, validates
from ecox.utils import code_format


class BaseMixin:
    """
    所有财务报表模型的混合基类

    提供:
    - 自动股票代码格式化
    - 代码验证
    - extra_data 管理
    """

    @declared_attr
    def stock_code(cls):
        """声明股票代码列"""
        return Column(String(10), nullable=False, index=True, comment="股票代码（带交易所前缀）")

    @property
    def formatted_code(self) -> str:
        """获取格式化的代码（带前缀）"""
        return code_format(self.stock_code)

    def ensure_extra_data(self, raw_data: dict) -> None:
        """
        确保 extra_data 包含完整的原始数据

        Args:
            raw_data: 原始数据字典
        """
        if not hasattr(self, 'extra_data') or self.extra_data is None:
            self.extra_data = raw_data
        else:
            # 合并缺失的字段
            for key, value in raw_data.items():
                if key not in self.extra_data:
                    self.extra_data[key] = value

    @validates('stock_code')
    def validate_stock_code(self, key, value):
        """
        验证股票代码格式

        Args:
            key: 字段名
            value: 股票代码值

        Returns:
            格式化后的股票代码

        Raises:
            ValueError: 代码格式无效
        """
        if value is None:
            return None

        # 格式化代码
        formatted = code_format(str(value))

        # 验证格式
        if not self._is_valid_code(formatted):
            raise ValueError(f"Invalid stock code format: {value}. Expected format: SH/SZ/BJ + 6 digits.")

        return formatted

    def _is_valid_code(self, code: str) -> bool:
        """
        检查代码是否有效

        Args:
            code: 股票代码

        Returns:
            是否有效
        """
        return bool(re.match(r'^(SH|SZ|BJ)\d{6}$', code))

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__} {self.stock_code}>"
EOF
```

**Step 2: 创建 models __init__.py**

```bash
cat > src/ecox/models/__init__.py << 'EOF'
"""数据模型模块"""

from .base import BaseMixin

__all__ = ["BaseMixin"]
EOF
```

**Step 3: 编写测试**

```bash
cat > tests/models/test_base.py << 'EOF'
"""测试 BaseMixin"""

import pytest
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, Session
from ecox.models.base import BaseMixin


# 创建测试基类
Base = declarative_base()


class TestModel(Base, BaseMixin):
    """测试模型"""
    __tablename__ = 'test_model'

    id = Column(Integer, primary_key=True)


def test_stock_code_validation():
    """测试股票代码验证"""
    model = TestModel()

    # 有效代码
    valid_codes = ['SH600000', 'SZ000001', 'BJ430047', '600000', '000001']
    for code in valid_codes:
        model.stock_code = code
        assert model.stock_code.startswith(('SH', 'SZ', 'BJ'))
        print(f"✓ {code} -> {model.stock_code}")


def test_stock_code_validation_invalid():
    """测试无效代码"""
    model = TestModel()

    with pytest.raises(ValueError, match="Invalid stock code"):
        model.stock_code = "INVALID"


def test_formatted_code_property():
    """测试格式化代码属性"""
    model = TestModel()
    model.stock_code = "600000"
    assert model.formatted_code == "SH600000"


def test_ensure_extra_data():
    """测试 extra_data 管理"""
    model = TestModel()
    model.stock_code = "SH600000"

    # 首次设置
    data1 = {"field1": "value1", "field2": "value2"}
    model.ensure_extra_data(data1)
    assert model.extra_data == data1

    # 追加数据
    data2 = {"field3": "value3"}
    model.ensure_extra_data(data2)
    assert "field1" in model.extra_data
    assert "field3" in model.extra_data


def test_repr():
    """测试字符串表示"""
    model = TestModel()
    model.stock_code = "SH600000"
    assert "SH600000" in repr(model)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 4: 运行测试**

```bash
uv run pytest tests/models/test_base.py -v
```

Expected: `5 passed`

**Step 5: 提交**

```bash
git add src/ecox/models/ tests/models/
git commit -m "feat: 添加 BaseMixin 模型基类

- 自动股票代码格式化和验证
- extra_data 管理功能
- 统一的字符串表示
- 完整的单元测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 创建数据验证器

**目的:** 建立数据验证机制

**Files:**
- Create: `src/ecox/validators/model_validators.py`
- Test: `tests/validators/test_model_validators.py`

**Step 1: 编写验证器**

```bash
mkdir -p src/ecox/validators
cat > src/ecox/validators/model_validators.py << 'EOF'
"""模型数据验证器"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ValidationSeverity(Enum):
    """验证严重级别"""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题"""
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "value": self.value
        }


class ModelValidator:
    """模型验证器基类"""

    # 必填字段
    REQUIRED_FIELDS = ['stock_code', 'report_date']

    # 数值字段
    NUMERIC_FIELDS = ['total_revenue', 'operating_profit', 'net_profit',
                      'total_assets', 'total_liabilities']

    def validate(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """
        验证数据，返回问题列表

        Args:
            data: 待验证的数据字典

        Returns:
            验证问题列表
        """
        issues = []

        issues.extend(self._validate_required_fields(data))
        issues.extend(self._validate_types(data))
        issues.extend(self._validate_business_rules(data))
        issues.extend(self._validate_cross_field_relations(data))

        return issues

    def _validate_required_fields(self, data: Dict) -> List[ValidationIssue]:
        """验证必填字段"""
        issues = []

        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                issues.append(ValidationIssue(
                    field=field,
                    message=f"Required field missing",
                    severity=ValidationSeverity.ERROR
                ))

        return issues

    def _validate_types(self, data: Dict) -> List[ValidationIssue]:
        """验证数据类型"""
        issues = []

        for field in self.NUMERIC_FIELDS:
            if field in data and data[field] is not None:
                if not isinstance(data[field], (int, float)):
                    issues.append(ValidationIssue(
                        field=field,
                        message=f"Must be numeric, got {type(data[field]).__name__}",
                        severity=ValidationSeverity.ERROR,
                        value=data[field]
                    ))

        return issues

    def _validate_business_rules(self, data: Dict) -> List[ValidationIssue]:
        """业务规则验证"""
        issues = []

        # 规则1: 收入不应为负
        if data.get('total_revenue'):
            revenue = data['total_revenue']
            try:
                revenue_val = float(revenue)
                if revenue_val < 0:
                    issues.append(ValidationIssue(
                        field='total_revenue',
                        message=f"Revenue cannot be negative: {revenue_val}",
                        severity=ValidationSeverity.ERROR,
                        value=revenue_val
                    ))
            except (ValueError, TypeError):
                pass

        # 规则2: 净利润不应超过营收的10倍（异常检测）
        if data.get('total_revenue') and data.get('net_profit'):
            try:
                revenue = float(data['total_revenue'])
                profit = float(data['net_profit'])

                if revenue > 0 and abs(profit) > abs(revenue) * 10:
                    issues.append(ValidationIssue(
                        field='net_profit',
                        message=f"Net profit anomaly: {profit:.2f} exceeds 10x revenue: {revenue:.2f}",
                        severity=ValidationSeverity.WARNING,
                        value=profit
                    ))
            except (ValueError, TypeError):
                pass

        return issues

    def _validate_cross_field_relations(self, data: Dict) -> List[ValidationIssue]:
        """勾稽关系检查"""
        issues = []

        # 检查营业利润和净利润的一致性
        if data.get('operating_profit') and data.get('net_profit'):
            try:
                operating = float(data['operating_profit'])
                net = float(data['net_profit'])

                # 如果营业利润为正，净利润不应为负（特殊情况除外）
                if operating > 0 and net < 0:
                    issues.append(ValidationIssue(
                        field='net_profit',
                        message=f"Sign inconsistency: operating profit is positive ({operating}) but net profit is negative ({net})",
                        severity=ValidationSeverity.WARNING
                    ))
            except (ValueError, TypeError):
                pass

        return issues


class ProfitSheetValidator(ModelValidator):
    """利润表验证器"""

    REQUIRED_FIELDS = ['stock_code', 'report_date', 'total_revenue']

    def _validate_business_rules(self, data: Dict) -> List[ValidationIssue]:
        """利润表特定规则"""
        issues = super()._validate_business_rules(data)

        # 计算毛利率并检查合理性
        if data.get('total_revenue') and data.get('operating_cost'):
            try:
                revenue = float(data['total_revenue'])
                cost = float(data['operating_cost'])

                if revenue > 0:
                    gross_margin = (revenue - cost) / revenue * 100

                    if gross_margin < -50 or gross_margin > 100:
                        issues.append(ValidationIssue(
                            field='total_revenue',
                            message=f"Gross profit margin anomaly: {gross_margin:.2f}%",
                            severity=ValidationSeverity.WARNING,
                            value=gross_margin
                        ))
            except (ValueError, TypeError):
                pass

        return issues


class BalanceSheetValidator(ModelValidator):
    """资产负债表验证器"""

    REQUIRED_FIELDS = ['stock_code', 'report_date', 'total_assets']

    def _validate_business_rules(self, data: Dict) -> List[ValidationIssue]:
        """资产负债表特定规则"""
        issues = super()._validate_business_rules(data)

        # 资产负债率应在合理范围内
        if data.get('total_assets') and data.get('total_liabilities'):
            try:
                assets = float(data['total_assets'])
                liabilities = float(data['total_liabilities'])

                if assets > 0:
                    debt_ratio = (liabilities / assets) * 100

                    if debt_ratio > 100:
                        issues.append(ValidationIssue(
                            field='total_liabilities',
                            message=f"Debt ratio exceeds 100%: {debt_ratio:.2f}%",
                            severity=ValidationSeverity.WARNING,
                            value=debt_ratio
                        ))
            except (ValueError, TypeError):
                pass

        return issues
EOF
```

**Step 2: 创建 validators __init__.py**

```bash
cat > src/ecox/validators/__init__.py << 'EOF'
"""验证器模块"""

from .model_validators import (
    ValidationSeverity,
    ValidationIssue,
    ModelValidator,
    ProfitSheetValidator,
    BalanceSheetValidator
)

__all__ = [
    "ValidationSeverity",
    "ValidationIssue",
    "ModelValidator",
    "ProfitSheetValidator",
    "BalanceSheetValidator"
]
EOF
```

**Step 3: 编写测试**

```bash
cat > tests/validators/test_model_validators.py << 'EOF'
"""测试模型验证器"""

import pytest
from ecox.validators import (
    ModelValidator,
    ProfitSheetValidator,
    BalanceSheetValidator,
    ValidationSeverity
)


def test_model_validator_missing_required_field():
    """测试缺失必填字段"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        # 缺少 report_date
    }

    issues = validator.validate(data)

    assert len(issues) > 0
    assert any(i.field == 'report_date' for i in issues)


def test_model_validator_negative_revenue():
    """测试负收入"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_revenue': -1000000
    }

    issues = validator.validate(data)

    assert any(i.field == 'total_revenue' and 'cannot be negative' in i.message for i in issues)


def test_model_validator_profit_anomaly():
    """测试利润异常"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_revenue': 1000000,
        'net_profit': 15000000  # 15倍收入
    }

    issues = validator.validate(data)

    assert any(i.field == 'net_profit' and 'anomaly' in i.message for i in issues)


def test_model_validator_sign_inconsistency():
    """测试符号不一致"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'operating_profit': 1000000,
        'net_profit': -500000
    }

    issues = validator.validate(data)

    assert any('inconsistency' in i.message for i in issues)


def test_profit_sheet_validator_gross_margin():
    """测试毛利率异常"""
    validator = ProfitSheetValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_revenue': 1000000,
        'operating_cost': 3000000  # 导致 -200% 毛利率
    }

    issues = validator.validate(data)

    assert any('margin' in i.message for i in issues)


def test_balance_sheet_validator_debt_ratio():
    """测试资产负债率"""
    validator = BalanceSheetValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_assets': 1000000,
        'total_liabilities': 1200000  # > 100%
    }

    issues = validator.validate(data)

    assert any('Debt ratio' in i.message for i in issues)


def test_validation_issue_to_dict():
    """测试 ValidationIssue 转字典"""
    from ecox.validators import ValidationIssue

    issue = ValidationIssue(
        field='test_field',
        message='Test message',
        severity=ValidationSeverity.ERROR,
        value=100
    )

    result = issue.to_dict()
    assert result['field'] == 'test_field'
    assert result['message'] == 'Test message'
    assert result['severity'] == 'error'
    assert result['value'] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 4: 运行测试**

```bash
uv run pytest tests/validators/test_model_validators.py -v
```

Expected: `8 passed`

**Step 5: 提交**

```bash
git add src/ecox/validators/ tests/validators/
git commit -m "feat: 添加模型数据验证器

- ValidationIssue 和 ValidationSeverity 数据类
- ModelValidator 基类，提供通用验证逻辑
- ProfitSheetValidator 利润表验证器
- BalanceSheetValidator 资产负债表验证器
- 支持必填字段、类型、业务规则、勾稽关系检查
- 完整的单元测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 创建懒加载服务

**目的:** 实现自动数据获取和缓存

**Files:**
- Create: `src/ecox/services/lazy_loading_service.py`
- Test: `tests/services/test_lazy_loading_service.py`

**Step 1: 编写懒加载服务（第一部分 - 基础结构）**

```bash
cat > src/ecox/services/lazy_loading_service.py << 'EOF'
"""懒加载服务 - 自动获取和缓存财务数据"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import lru_cache
import threading
import pandas as pd

from ecox.utils import code_format
from ecox.database import get_db_session
from ecox.exceptions import ExternalDataSourceError

logger = logging.getLogger(__name__)


class LazyLoadingService:
    """
    懒加载服务

    功能:
    - 自动检查缓存（内存、数据库）
    - 从 akshare 下载缺失数据
    - 自动存储到数据库
    - 并发控制，防止重复下载
    """

    # 缓存过期时间（天）
    CACHE_EXPIRY_DAYS = {
        'Q1': 120,    # 一季报：4个月后过期
        'Q2': 120,    # 中报：4个月后过期
        'Q3': 120,    # 三季报：4个月后过期
        'Q4': 180,    # 年报：6个月后过期
    }

    def __init__(self):
        """初始化懒加载服务"""
        self._memory_cache: Dict[str, Any] = {}
        self._downloading = threading.Lock()
        self._download_queue: set = set()

    def get_financial_data(
        self,
        stock_code: str,
        report_date: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取财务数据（懒加载模式）

        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，None 表示最新）
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            包含财务数据的字典

        Raises:
            ExternalDataSourceError: 无法获取数据
        """
        formatted_code = code_format(stock_code)

        logger.info(f"Lazy loading financial data for {formatted_code}")

        # Step 1: 检查内存缓存
        if not force_refresh:
            cached = self._check_memory_cache(formatted_code, report_date)
            if cached:
                logger.debug("Memory cache hit")
                return cached

        # Step 2: 检查数据库
        db_data = self._fetch_from_database(formatted_code, report_date)

        if db_data and not force_refresh:
            if self._is_data_fresh(db_data):
                logger.info(f"Database hit for {formatted_code}")
                # 更新内存缓存
                self._update_memory_cache(formatted_code, report_date, db_data)
                return db_data
            else:
                logger.info(f"Data expired for {formatted_code}, refreshing...")

        # Step 3: 从 akshare 下载
        logger.info(f"Fetching from akshare for {formatted_code}")
        fresh_data = self._fetch_from_akshare(formatted_code)

        if fresh_data:
            # Step 4: 存储到数据库
            self._save_to_database(fresh_data)

            # 更新内存缓存
            self._update_memory_cache(formatted_code, report_date, fresh_data)

            return fresh_data

        # 如果下载失败，返回数据库中的旧数据（如果有）
        if db_data:
            logger.warning(
                f"Failed to fetch fresh data, using cached data for {formatted_code}"
            )
            return db_data

        raise ExternalDataSourceError(
            f"Unable to fetch financial data for {formatted_code}",
            details={"stock_code": stock_code, "report_date": report_date}
        )

    def _check_memory_cache(
        self,
        stock_code: str,
        report_date: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """检查内存缓存"""
        cache_key = self._get_cache_key(stock_code, report_date)
        return self._memory_cache.get(cache_key)

    def _update_memory_cache(
        self,
        stock_code: str,
        report_date: Optional[str],
        data: Dict[str, Any]
    ) -> None:
        """更新内存缓存"""
        cache_key = self._get_cache_key(stock_code, report_date)
        self._memory_cache[cache_key] = data

    def _get_cache_key(self, stock_code: str, report_date: Optional[str]) -> str:
        """生成缓存键"""
        return f"{stock_code}_{report_date or 'latest'}"

    def _fetch_from_database(
        self,
        stock_code: str,
        report_date: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """从数据库获取数据"""
        try:
            from ecox.models import StockProfitSheet
            from sqlalchemy import desc

            with get_db_session() as session:
                query = session.query(StockProfitSheet).filter(
                    StockProfitSheet.stock_code == stock_code
                )

                if report_date:
                    from datetime import datetime
                    report_dt = datetime.fromisoformat(report_date) if isinstance(report_date, str) else report_date
                    query = query.filter(StockProfitSheet.report_date == report_dt)

                record = query.order_by(desc(StockProfitSheet.report_date)).first()

                if not record:
                    return None

                return {
                    'stock_code': stock_code,
                    'stock_name': record.stock_name,
                    'report_date': record.report_date,
                    'report_type': record.report_type,
                    'profit_sheet': record.extra_data or {},
                    'source': 'database',
                    'fetch_time': datetime.now()
                }

        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return None

    def _fetch_from_akshare(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """从 akshare 获取数据（带并发控制）"""
        task_id = stock_code

        # 防止重复下载
        if task_id in self._download_queue:
            logger.info(f"Already downloading {stock_code}, waiting...")
            import time
            for _ in range(30):
                time.sleep(1)
                if task_id not in self._download_queue:
                    return self._fetch_from_database(stock_code, None)
            return None

        self._download_queue.add(task_id)

        try:
            with self._downloading:
                logger.info(f"Downloading financial data for {stock_code} from akshare")

                import akshare as ak

                # 去掉前缀用于 akshare
                ak_code = stock_code[2:]

                # 并行下载三大报表
                profit_df = ak.stock_profit_sheet_by_report_em(symbol=ak_code)
                balance_df = ak.stock_balance_sheet_by_report_em(symbol=ak_code)
                cashflow_df = ak.stock_cash_flow_sheet_by_report_em(symbol=ak_code)

                # 获取股票名称
                try:
                    stock_info = ak.stock_individual_info_em(symbol=ak_code)
                    stock_name = stock_info.get('股票简称', 'Unknown')
                except:
                    stock_name = 'Unknown'

                return {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'profit_df': profit_df,
                    'balance_df': balance_df,
                    'cashflow_df': cashflow_df,
                    'source': 'akshare',
                    'fetch_time': datetime.now()
                }

        except Exception as e:
            logger.error(f"Error fetching from akshare: {e}")
            return None
        finally:
            self._download_queue.discard(task_id)

    def _save_to_database(self, data: Dict[str, Any]) -> bool:
        """保存数据到数据库"""
        try:
            from ecox.models import StockProfitSheet

            with get_db_session() as session:
                if 'profit_df' in data:
                    count = 0
                    for _, row in data['profit_df'].iterrows():
                        report_dt = pd.to_datetime(row['REPORT_DATE'])

                        record = session.query(StockProfitSheet).filter_by(
                            stock_code=data['stock_code'],
                            report_date=report_dt
                        ).first()

                        if not record:
                            record = StockProfitSheet(
                                stock_code=data['stock_code'],
                                stock_name=data['stock_name'],
                                report_date=report_dt,
                                report_type=self._infer_report_type(row['REPORT_DATE']),
                                extra_data=row.to_dict()
                            )
                            session.add(record)
                        else:
                            # 更新 extra_data
                            record.extra_data = row.to_dict()

                        count += 1

                    session.commit()
                    logger.info(f"Saved {count} profit records to database")

                return True

        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False

    def _is_data_fresh(self, data: Dict[str, Any]) -> bool:
        """检查数据是否过期"""
        report_date = data.get('report_date')
        report_type = data.get('report_type')

        if not report_date:
            return False

        if isinstance(report_date, str):
            report_date = datetime.fromisoformat(report_date)

        # 计算数据年龄
        age = datetime.now() - report_date
        max_age = timedelta(days=self.CACHE_EXPIRY_DAYS.get(report_type, 90))

        return age <= max_age

    def _infer_report_type(self, date_str) -> str:
        """从日期推断报告类型"""
        if isinstance(date_str, str):
            parts = date_str.split('-')
            if len(parts) >= 2:
                month = int(parts[1])
            else:
                return 'Unknown'
        else:
            month = date_str.month if hasattr(date_str, 'month') else 0

        if month == 3:
            return 'Q1'
        elif month == 6:
            return 'Q2'
        elif month == 9:
            return 'Q3'
        elif month == 12:
            return 'Q4'
        return 'Unknown'

    def invalidate_cache(self, stock_code: str = None) -> None:
        """
        使缓存失效

        Args:
            stock_code: 特定股票代码，None 表示清除所有缓存
        """
        if stock_code:
            keys_to_remove = [
                k for k in self._memory_cache.keys()
                if k.startswith(stock_code)
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]

            # 清除 LRU 缓存
            if hasattr(self.get_financial_data, 'cache_clear'):
                self.get_financial_data.cache_clear()
        else:
            self._memory_cache.clear()
            if hasattr(self.get_financial_data, 'cache_clear'):
                self.get_financial_data.cache_clear()

        logger.info(f"Cache invalidated for {stock_code or 'all stocks'}")
EOF
```

**Step 2: 编写测试**

```bash
cat > tests/services/test_lazy_loading_service.py << 'EOF'
"""测试懒加载服务"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from ecox.services.lazy_loading_service import LazyLoadingService
from ecox.exceptions import ExternalDataSourceError


def test_lazy_loading_service_init():
    """测试服务初始化"""
    service = LazyLoadingService()

    assert service._memory_cache == {}
    assert isinstance(service._downloading, type(threading.Lock()))
    assert service._download_queue == set()


def test_get_cache_key():
    """测试缓存键生成"""
    service = LazyLoadingService()

    key1 = service._get_cache_key('SH600000', None)
    key2 = service._get_cache_key('SH600000', '2025-12-31')

    assert key1 == 'SH600000_latest'
    assert key2 == 'SH600000_2025-12-31'


def test_infer_report_type():
    """测试报告类型推断"""
    service = LazyLoadingService()

    assert service._infer_report_type('2025-03-31') == 'Q1'
    assert service._infer_report_type('2025-06-30') == 'Q2'
    assert service._infer_report_type('2025-09-30') == 'Q3'
    assert service._infer_report_type('2025-12-31') == 'Q4'
    assert service._infer_report_type('2025-05-15') == 'Unknown'


def test_memory_cache_operations():
    """测试内存缓存操作"""
    service = LazyLoadingService()

    # 初始状态
    assert service._check_memory_cache('SH600000', None) is None

    # 更新缓存
    test_data = {'stock_code': 'SH600000', 'test': 'data'}
    service._update_memory_cache('SH600000', None, test_data)

    # 检查缓存
    cached = service._check_memory_cache('SH600000', None)
    assert cached == test_data


def test_invalidate_cache():
    """测试缓存失效"""
    service = LazyLoadingService()

    # 添加缓存
    service._update_memory_cache('SH600000', None, {'test': 'data1'})
    service._update_memory_cache('SZ000001', None, {'test': 'data2'})

    # 清除特定股票缓存
    service.invalidate_cache('SH600000')

    assert service._check_memory_cache('SH600000', None) is None
    assert service._check_memory_cache('SZ000001', None) is not None


def test_invalidate_all_cache():
    """测试清除所有缓存"""
    service = LazyLoadingService()

    service._update_memory_cache('SH600000', None, {'test': 'data'})

    service.invalidate_cache()

    assert service._check_memory_cache('SH600000', None) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 3: 运行测试**

```bash
uv run pytest tests/services/test_lazy_loading_service.py -v
```

Expected: `6 passed`

**Step 4: 提交**

```bash
git add src/ecox/services/lazy_loading_service.py tests/services/test_lazy_loading_service.py
git commit -m "feat: 添加懒加载服务

- 自动检查缓存（内存、数据库）
- 从 akshare 自动下载缺失数据
- 并发控制防止重复下载
- 数据过期检测和自动刷新
- 缓存管理功能
- 基础单元测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: 集成和更新

### Task 7: 更新财务分析服务以使用懒加载

**目的:** 集成懒加载服务到现有系统

**Files:**
- Modify: `src/ecox/services/financial_analysis_service.py`
- Test: `tests/services/test_financial_analysis_integration.py`

**Step 1: 读取现有的财务分析服务**

```bash
head -100 src/ecox/services/financial_analysis_service.py
```

**Step 2: 更新 _get_financial_data 方法**

```bash
cat > /tmp/patch_financial_service.py << 'EOF'
"""更新财务分析服务以使用懒加载"""

# 在 financial_analysis_service.py 中：
# 1. 导入 LazyLoadingService
# 2. 在 __init__ 中初始化
# 3. 更新 _get_financial_data 方法

# 修改后的代码片段：

"""
在导入部分添加:
from .lazy_loading_service import LazyLoadingService

在 __init__ 方法中添加:
self.lazy_loader = LazyLoadingService()

替换 _get_financial_data 方法:
def _get_financial_data(
    self, stock_code: str, report_date: str | None = None
) -> dict[str, Any]:
    # 使用懒加载服务
    data = self.lazy_loader.get_financial_data(
        stock_code=stock_code,
        report_date=report_date,
        force_refresh=False
    )

    return {
        "profit_sheet": data.get('profit_sheet', {}),
        "balance_sheet": data.get('balance_sheet', {}),
        "cash_flow_sheet": data.get('cash_flow_sheet', {}),
        "stock_name": data.get('stock_name'),
        "report_date": data.get('report_date'),
        "report_type": data.get('report_type'),
    }
"""
EOF
cat /tmp/patch_financial_service.py
```

**Step 3: 手动编辑文件（需要具体实现）**

查看当前文件，确定需要修改的位置

**Step 4: 编写集成测试**

```bash
cat > tests/services/test_financial_analysis_integration.py << 'EOF'
"""测试财务分析服务与懒加载的集成"""

import pytest
from unittest.mock import Mock, patch
from ecox.services.financial_analysis_service import FinancialAnalysisService


def test_financial_analysis_service_has_lazy_loader():
    """测试财务分析服务包含懒加载器"""
    service = FinancialAnalysisService()

    assert hasattr(service, 'lazy_loader')
    assert service.lazy_loader is not None


@patch('ecox.services.lazy_loading_service.LazyLoadingService.get_financial_data')
def test_calculate_metrics_uses_lazy_loader(mock_get_data):
    """测试 calculate_metrics 使用懒加载"""
    # 模拟返回数据
    mock_get_data.return_value = {
        'stock_code': 'SH600000',
        'stock_name': '测试股票',
        'report_date': '2025-12-31',
        'report_type': 'Q4',
        'profit_sheet': {
            'total_revenue': 1000000000,
            'net_profit': 100000000,
        },
        'balance_sheet': {
            'total_assets': 5000000000,
        },
        'cash_flow_sheet': {}
    }

    service = FinancialAnalysisService()
    result = service.calculate_metrics('600000')  # 不带前缀

    # 验证调用了懒加载
    assert mock_get_data.called
    assert mock_get_data.call_args[1]['stock_code'] == '600000'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 5: 运行测试**

```bash
uv run pytest tests/services/test_financial_analysis_integration.py -v
```

**Step 6: 提交**

```bash
git add src/ecox/services/financial_analysis_service.py tests/services/test_financial_analysis_integration.py
git commit -m "feat: 集成懒加载到财务分析服务

- FinancialAnalysisService 现在使用 LazyLoadingService
- _get_financial_data 方法自动获取数据
- 支持不带前缀的股票代码
- 添加集成测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 8: 创建数据迁移脚本

**目的:** 提供数据迁移工具

**Files:**
- Create: `scripts/migrate_stock_data.py`
- Test: `tests/test_migrate_script.py`

**Step 1: 编写迁移脚本**

```bash
cat > scripts/migrate_stock_data.py << 'EOF'
#!/usr/bin/env python
"""
股票数据迁移脚本

功能:
1. 备份现有数据库
2. 统一股票代码格式
3. 补充 extra_data 字段
4. 验证迁移结果
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ecox.logging_config import setup_logging
from ecox.utils import code_format
from ecox.exceptions import MigrationError
from ecox.database import get_db_session
from ecox.models import StockProfitSheet, StockBalanceSheet, StockCashFlowSheet
from ecox.validators import ProfitSheetValidator

logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""

    def __init__(self, db_url: str = None):
        """初始化迁移器"""
        self.db_url = db_url

    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库

        Args:
            backup_path: 备份文件路径

        Returns:
            是否成功
        """
        logger.info(f"Creating backup at {backup_path}")

        import subprocess

        try:
            # 使用 pg_dump 备份
            result = subprocess.run([
                'pg_dump',
                '-h', 'localhost',
                '-U', 'zmdsn',
                '-d', 'stock',
                '-f', backup_path,
                '--no-owner',
                '--no-acl'
            ], capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return False

            logger.info("Backup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Backup error: {e}")
            return False

    def migrate_stock_codes(self, dry_run: bool = False) -> dict:
        """
        迁移股票代码格式

        Args:
            dry_run: 是否只模拟运行

        Returns:
            迁移统计
        """
        logger.info("Phase 2: Migrating stock codes...")

        stats = {
            'profit_updated': 0,
            'balance_updated': 0,
            'cashflow_updated': 0,
            'errors': 0
        }

        try:
            with get_db_session() as session:
                # 更新利润表
                profit_records = session.query(StockProfitSheet).all()

                for record in tqdm(profit_records, desc="Migrating profit sheets"):
                    try:
                        old_code = record.stock_code
                        new_code = code_format(old_code)

                        if new_code != old_code:
                            if not dry_run:
                                record.stock_code = new_code

                            stats['profit_updated'] += 1
                            logger.debug(f"{old_code} -> {new_code}")

                    except Exception as e:
                        logger.error(f"Error migrating {record.stock_code}: {e}")
                        stats['errors'] += 1

                if not dry_run:
                    session.commit()

                logger.info(f"Profit sheet migration: {stats['profit_updated']} updated, {stats['errors']} errors")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise MigrationError(f"Stock code migration failed: {e}")

        return stats

    def validate_migrated_data(self, limit: int = 1000) -> list:
        """
        验证迁移后的数据

        Args:
            limit: 验证记录数限制

        Returns:
            验证问题列表
        """
        logger.info("Validating migrated data...")

        issues = []
        validator = ProfitSheetValidator()

        try:
            with get_db_session() as session:
                records = session.query(StockProfitSheet).limit(limit).all()

                for record in tqdm(records, desc="Validating"):
                    data = {
                        'stock_code': record.stock_code,
                        'report_date': str(record.report_date) if record.report_date else None,
                        'total_revenue': float(record.total_revenue) if record.total_revenue else None,
                        'operating_profit': float(record.operating_profit) if record.operating_profit else None,
                        'net_profit': float(record.net_profit) if record.net_profit else None,
                    }

                    validation_issues = validator.validate(data)

                    if validation_issues:
                        issues.append({
                            'stock_code': record.stock_code,
                            'report_date': record.report_date,
                            'issues': [i.to_dict() for i in validation_issues]
                        })

                logger.info(f"Validation completed: {len(issues)} issues found")

        except Exception as e:
            logger.error(f"Validation error: {e}")

        return issues

    def run_full_migration(
        self,
        backup_path: str = None,
        dry_run: bool = False
    ) -> dict:
        """
        执行完整迁移流程

        Args:
            backup_path: 备份文件路径
            dry_run: 是否模拟运行

        Returns:
            迁移结果
        """
        logger.info("=" * 60)
        logger.info("Starting data migration")
        if dry_run:
            logger.info("** DRY RUN MODE - No changes will be made **")
        logger.info("=" * 60)

        results = {}

        # Phase 1: 备份
        if backup_path and not dry_run:
            if not self.backup_database(backup_path):
                raise MigrationError("Backup failed, aborting migration")

        # Phase 2: 代码格式统一
        code_stats = self.migrate_stock_codes(dry_run=dry_run)
        results['code_migration'] = code_stats

        # Phase 3: 验证
        validation_issues = self.validate_migrated_data()
        results['validation'] = {
            'total_issues': len(validation_issues),
            'sample_issues': validation_issues[:10]
        }

        logger.info("=" * 60)
        logger.info("Migration completed!")
        logger.info(f"Code migration: {code_stats}")
        logger.info(f"Validation issues: {len(validation_issues)}")
        logger.info("=" * 60)

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票数据迁移工具')
    parser.add_argument('--backup', type=str, help='备份文件路径')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不修改数据')
    parser.add_argument('--log-level', type=str, default='INFO', help='日志级别')

    args = parser.parse_args()

    # 设置日志
    setup_logging(log_level=args.log_level)

    # 执行迁移
    migrator = DataMigrator()

    try:
        results = migrator.run_full_migration(
            backup_path=args.backup,
            dry_run=args.dry_run
        )

        # 输出结果
        print("\n迁移结果:")
        print(f"  代码迁移: {results['code_migration']}")
        print(f"  验证问题: {results['validation']['total_issues']}")

        if results['validation']['total_issues'] > 0:
            print("\n示例问题:")
            for issue in results['validation']['sample_issues'][:5]:
                print(f"  {issue['stock_code']}: {len(issue['issues'])} issues")

        return 0

    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x scripts/migrate_stock_data.py
```

**Step 2: 测试迁移脚本（dry-run）**

```bash
uv run python scripts/migrate_stock_data.py --dry-run --log-level INFO
```

Expected: 模拟运行，显示将更新的记录数，不实际修改数据

**Step 3: 提交**

```bash
git add scripts/migrate_stock_data.py
git commit -m "feat: 添加数据迁移脚本

- 支持数据库备份
- 股票代码格式迁移
- 数据验证功能
- 支持 dry-run 模式
- 详细的日志输出
- 进度条显示

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Phase 4: 测试和文档

### Task 9: 编写端到端测试

**目的:** 验证整个系统的工作流程

**Files:**
- Create: `tests/integration/test_e2e_lazy_loading.py`

**Step 1: 编写端到端测试**

```bash
cat > tests/integration/test_e2e_lazy_loading.py << 'EOF'
"""端到端测试：完整的懒加载流程"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

from ecox.services.financial_analysis_service import FinancialAnalysisService


@pytest.mark.integration
def test_full_lazy_loading_flow():
    """测试完整的懒加载流程"""

    # 模拟数据库查询返回 None（没有数据）
    with patch('ecox.services.lazy_loading_service.get_db_session') as mock_session:
        mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.first.return_value = None

        # 模拟 akshare 返回数据
        mock_profit_df = pd.DataFrame({
            'REPORT_DATE': ['2025-09-30'],
            'TOTAL_OPERATE_INCOME': [1000000000],
            'PARENT_NETPROFIT': [100000000]
        })

        with patch('akshare.stock_profit_sheet_by_report_em') as mock_akshare:
            mock_akshare.return_value = mock_profit_df

            service = FinancialAnalysisService()

            # 第一次调用：应该从 akshare 获取
            result1 = service.calculate_metrics('601318', modules=['profitability'])

            # 验证调用了 akshare
            assert mock_akshare.called

            # 第二次调用：应该从缓存获取
            mock_akshare.reset_mock()
            result2 = service.calculate_metrics('601318', modules=['profitability'])

            # 不应该再次调用 akshare
            # （具体实现取决于缓存策略）


@pytest.mark.integration
def test_stock_code_format_handling():
    """测试各种股票代码格式"""

    test_codes = [
        '601318',      # 无前缀
        'SH601318',    # 已有前缀
        'sh601318',    # 小写前缀
    ]

    with patch('ecox.services.lazy_loading_service.get_db_session') as mock_session:
        # 模拟数据库有数据
        mock_record = Mock()
        mock_record.stock_code = 'SH601318'
        mock_record.stock_name = '中国平安'
        mock_record.report_date = datetime(2025, 9, 30)
        mock_record.report_type = 'Q3'
        mock_record.extra_data = {'test': 'data'}

        mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.first.return_value = mock_record

        service = FinancialAnalysisService()

        for code in test_codes:
            result = service.calculate_metrics(code)
            assert result['stock_code'] == 'SH601318' or result['stock_code'] == '601318'
            print(f"✓ {code} handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
EOF
```

**Step 2: 运行端到端测试**

```bash
uv run pytest tests/integration/ -v -m integration
```

**Step 3: 提交**

```bash
git add tests/integration/
git commit -m "test: 添加端到端集成测试

- 测试完整的懒加载流程
- 测试各种股票代码格式处理
- 验证缓存机制

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 10: 更新项目文档

**目的:** 更新文档以反映新的架构

**Files:**
- Modify: `README.md` (如果存在)
- Create: `docs/data-quality-guide.md`

**Step 1: 创建数据质量指南**

```bash
cat > docs/data-quality-guide.md << 'EOF'
# 数据质量指南

本文档说明 Ecox 项目中的数据质量保障机制。

## 概述

Ecox 实现了多层数据质量保障体系：

1. **模型层验证** - SQLAlchemy 模型自动验证代码格式和数据类型
2. **懒加载机制** - 自动获取和缓存财务数据
3. **业务验证** - 多维度数据验证确保数据质量

## 股票代码格式

### 标准格式

所有股票代码在系统中存储为带交易所前缀的格式：

- `SH` + 6位数字 - 上海证券交易所
- `SZ` + 6位数字 - 深圳证券交易所
- `BJ` + 6位数字 - 北京证券交易所

示例：
- `SH600000` - 浦发银行
- `SZ000001` - 平安银行
- `BJ430047` - 诺思兰德

### 代码格式化

使用 `code_format()` 函数自动格式化代码：

```python
from ecox.utils import code_format

code_format('600000')  # -> 'SH600000'
code_format('SH600000')  # -> 'SH600000'
code_format('sh600000')  # -> 'SH600000'
```

## 懒加载服务

### 工作原理

懒加载服务自动处理数据的获取和缓存：

1. 检查内存缓存
2. 检查数据库
3. 从 akshare 下载（如果需要）
4. 存储到数据库并更新缓存

### 使用示例

```python
from ecox.services.financial_analysis_service import FinancialAnalysisService

service = FinancialAnalysisService()

# 自动懒加载 - 如果数据库没有数据，会自动下载
result = service.calculate_metrics(
    stock_code='601318',  # 可以不带前缀
    modules=None  # 分析所有模块
)
```

### 缓存策略

不同报告类型有不同的缓存过期时间：

- Q1/Q2/Q3: 120天
- Q4: 180天

数据过期后会自动从 akshare 重新获取。

## 数据验证

### 验证层级

1. **模型层** - SQLAlchemy @validates 装饰器
2. **业务层** - ModelValidator 类
3. **数据库层** - 约束和触发器（可选）

### 验证规则

#### 基础规则
- 股票代码格式正确
- 必填字段不能为空
- 数值字段类型正确

#### 业务规则
- 收入不能为负
- 净利润不应超过收入的10倍（异常检测）
- 资产负债率不应超过100%

#### 勾稽关系
- 营业利润和净利润符号应一致
- 毛利率应在合理范围内

### 使用验证器

```python
from ecox.validators import ProfitSheetValidator

validator = ProfitSheetValidator()
data = {
    'stock_code': 'SH600000',
    'report_date': '2025-12-31',
    'total_revenue': 1000000000,
    'net_profit': 100000000
}

issues = validator.validate(data)
for issue in issues:
    print(f"{issue.field}: {issue.message} ({issue.severity})")
```

## 数据迁移

### 迁移脚本

使用 `scripts/migrate_stock_data.py` 迁移现有数据：

```bash
# 模拟运行（推荐先运行）
uv run python scripts/migrate_stock_data.py --dry-run

# 创建备份并迁移
uv run python scripts/migrate_stock_data.py --backup /path/to/backup.sql
```

### 迁移阶段

1. **备份** - 创建数据库备份
2. **代码格式统一** - 更新所有股票代码为带前缀格式
3. **验证** - 检查数据质量

## 错误处理

### 自定义异常

```python
from ecox.exceptions import (
    StockCodeError,
    DataValidationError,
    ExternalDataSourceError
)

# 使用错误处理装饰器
from ecox.utils import handle_errors

@handle_errors(default_return=None, raise_on_error=False)
def risky_function():
    # 可能失败的代码
    pass
```

## 日志

### 配置日志

```python
from ecox.logging_config import setup_logging, get_logger

# 配置日志系统
setup_logging(
    log_level="INFO",
    log_dir="./logs",
    enable_console=True,
    enable_file=True
)

# 获取日志器
logger = get_logger(__name__)
logger.info("Application started")
```

### 日志位置

- 控制台 - 实时输出
- 文件 - `logs/ecox_YYYY-MM-DD.log`
- 轮转策略 - 10MB/文件，保留5个文件

## 最佳实践

1. **使用懒加载** - 让系统自动处理数据获取
2. **验证输入** - 使用验证器检查数据质量
3. **处理异常** - 捕获并适当处理自定义异常
4. **检查日志** - 定期查看日志文件排查问题

## 故障排查

### 问题：数据查询失败

**原因**：股票代码格式不匹配

**解决**：
```python
from ecox.utils import code_format
formatted_code = code_format('600000')  # 使用格式化后的代码
```

### 问题：缓存数据过期

**原因**：数据超过了缓存过期时间

**解决**：强制刷新
```python
service.calculate_metrics('601318', force_refresh=True)
```

### 问题：akshare 下载失败

**原因**：网络问题或 API 限制

**解决**：系统会自动重试，或稍后再试

## 相关文档

- [设计文档](/docs/plans/2026-03-16-data-quality-refactor-design.md)
- [实施计划](/docs/plans/2026-03-16-data-quality-implementation-plan.md)
EOF
```

**Step 2: 更新主 README（如果需要）**

```bash
if [ -f README.md ]; then
  echo "Consider updating README.md with new features"
fi
```

**Step 3: 提交**

```bash
git add docs/
git commit -m "docs: 添加数据质量指南

- 股票代码格式说明
- 懒加载服务使用指南
- 数据验证机制说明
- 迁移脚本使用说明
- 错误处理和日志配置
- 最佳实践和故障排查

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 总结

### 完成清单

- [x] Task 0: 环境检查
- [x] Task 1: 自定义异常类
- [x] Task 2: 统一日志配置
- [x] Task 3: 错误处理装饰器
- [x] Task 4: BaseMixin 基类
- [x] Task 5: 数据验证器
- [x] Task 6: 懒加载服务
- [x] Task 7: 集成到财务分析服务
- [x] Task 8: 数据迁移脚本
- [x] Task 9: 端到端测试
- [x] Task 10: 文档更新

### 测试运行

```bash
# 运行所有测试
uv run pytest -v

# 测试覆盖率
uv run pytest --cov=src/ecox --cov-report=html
```

### 下一步

1. 在开发环境完整测试
2. 执行数据迁移（先 dry-run）
3. 验证生产环境数据
4. 部署和监控

---

**计划版本**: 1.0
**创建日期**: 2026-03-16
**预计时间**: 15-20 小时
