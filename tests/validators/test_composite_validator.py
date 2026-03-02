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
            "low_price": 9.0,
            "volume": -1000,  # 错误
        }
        result = validator.validate(data)

        assert result.is_valid is False
        assert len(result.errors) >= 2  # 至少有价格和成交量错误
