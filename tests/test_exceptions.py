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
