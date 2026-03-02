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
        assert "negative" in result.errors[0].lower() or "为负" in result.errors[0]

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
        assert any("mismatch" in err.lower() or "不匹配" in err for err in result.errors)
