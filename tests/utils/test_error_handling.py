"""测试错误处理装饰器"""

from __future__ import annotations
import pytest
from ecox.error_handling import handle_errors, retry_on_failure
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
