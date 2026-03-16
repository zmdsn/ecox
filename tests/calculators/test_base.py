"""BaseCalculator 基类单元测试"""

import pytest
from abc import ABC

from ecox.calculators.base import BaseCalculator


class TestBaseCalculator:
    """测试 BaseCalculator 基类"""

    def test_is_abstract_class(self):
        """验证 BaseCalculator 是抽象类"""
        assert issubclass(BaseCalculator, ABC)
        # 验证有抽象方法
        assert hasattr(BaseCalculator, "calculate")

    def test_cannot_instantiate_directly(self):
        """验证不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            BaseCalculator()

    def test_round_with_float(self):
        """测试 _round 方法保留4位小数"""
        result = BaseCalculator._round(0.123456)
        assert result == 0.1235

    def test_round_with_none(self):
        """测试 _round 方法处理 None"""
        result = BaseCalculator._round(None)
        assert result is None

    def test_round_with_integer(self):
        """测试 _round 方法处理整数"""
        result = BaseCalculator._round(123)
        assert result == 123.0

    def test_safe_float_with_integer(self):
        """测试 _safe_float 方法转换整数"""
        result = BaseCalculator._safe_float(123)
        assert result == 123.0
        assert isinstance(result, float)

    def test_safe_float_with_none(self):
        """测试 _safe_float 方法处理 None"""
        result = BaseCalculator._safe_float(None)
        assert result is None

    def test_safe_float_with_invalid_string(self):
        """测试 _safe_float 方法处理无效字符串"""
        result = BaseCalculator._safe_float("N/A")
        assert result is None

    def test_safe_float_with_valid_string(self):
        """测试 _safe_float 方法处理有效字符串"""
        result = BaseCalculator._safe_float("123.45")
        assert result == 123.45

    def test_safe_float_with_float(self):
        """测试 _safe_float 方法处理浮点数"""
        result = BaseCalculator._safe_float(123.456)
        assert result == 123.456


class ConcreteCalculator(BaseCalculator):
    """用于测试的具体计算器实现"""

    def calculate(
        self,
        profit_sheet: dict,
        balance_sheet: dict,
        cash_flow_sheet: dict,
        market_data: dict | None = None,
    ) -> dict:
        """测试实现"""
        return {"test": "result"}


class TestConcreteCalculator:
    """测试具体实现类"""

    def test_can_instantiate_concrete(self):
        """验证可以实例化具体实现类"""
        calculator = ConcreteCalculator()
        assert isinstance(calculator, BaseCalculator)

    def test_calculate_method(self):
        """验证 calculate 方法可以调用"""
        calculator = ConcreteCalculator()
        result = calculator.calculate({}, {}, {})
        assert result == {"test": "result"}
