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
        """测试价格为零（应产生错误）"""
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
