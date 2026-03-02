"""数据验证集成测试

测试验证器与数据库、服务的集成
"""
import pytest
from datetime import date, datetime
from decimal import Decimal

from ecox.validators.price_validator import PriceValidator
from ecox.validators.volume_validator import VolumeValidator
from ecox.validators.composite import CompositeValidator
from ecox.config import ValidationConfig, config


@pytest.fixture
def validation_config():
    """创建测试用的验证配置"""
    config = ValidationConfig()
    config.STRICT_MODE = False
    config.AUTO_CLEAN = True
    return config


@pytest.fixture
def sample_valid_data():
    """创建有效的测试数据"""
    return {
        "stock_code": "000001",
        "trade_date": date(2024, 1, 1),
        "open_price": 10.50,
        "high_price": 11.00,
        "low_price": 10.20,
        "close_price": 10.80,
        "volume": 1000000,
        "amount": 10800000.0,
    }


class TestValidationIntegration:
    """验证器集成测试"""

    def test_price_validator_with_config(self, validation_config, sample_valid_data):
        """测试价格验证器使用配置"""
        validator = PriceValidator(validation_config)

        result = validator.validate(sample_valid_data)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_price_validator_config_range(self, validation_config):
        """测试配置的价格范围验证"""
        # 修改配置以测试范围
        validation_config.MIN_PRICE = 1.0
        validation_config.MAX_PRICE = 100.0

        validator = PriceValidator(validation_config)

        # 测试低于最小价格
        data = {
            "open_price": 0.5,
            "high_price": 1.0,
            "low_price": 0.5,
            "close_price": 0.8,
        }
        result = validator.validate(data)
        assert not result.is_valid
        assert any("out of range" in error for error in result.errors)

        # 测试高于最大价格
        data = {
            "open_price": 150.0,
            "high_price": 150.0,
            "low_price": 150.0,
            "close_price": 150.0,
        }
        result = validator.validate(data)
        assert not result.is_valid

    def test_volume_validator_with_config(self, validation_config, sample_valid_data):
        """测试成交量验证器使用配置"""
        validator = VolumeValidator(validation_config)

        result = validator.validate(sample_valid_data)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_volume_validator_config_range(self, validation_config):
        """测试配置的成交量范围验证"""
        validation_config.MAX_VOLUME = 100000

        validator = VolumeValidator(validation_config)

        # 测试超过最大成交量
        data = {
            "volume": 200000,
            "amount": 1000000.0,
            "close_price": 10.0,
        }
        result = validator.validate(data)
        assert not result.is_valid
        assert any("超过最大值" in error for error in result.errors)

    def test_composite_validator_integration(self, validation_config, sample_valid_data):
        """测试组合验证器集成"""
        validators = [PriceValidator(validation_config), VolumeValidator(validation_config)]
        composite = CompositeValidator(validators)

        result = composite.validate(sample_valid_data)
        assert result.is_valid

    def test_composite_validator_invalid_data(self, validation_config):
        """测试组合验证器处理无效数据"""
        validators = [PriceValidator(validation_config), VolumeValidator(validation_config)]
        composite = CompositeValidator(validators)

        # 创建无效数据（价格和成交量都有问题）
        invalid_data = {
            "stock_code": "000001",
            "trade_date": date(2024, 1, 1),
            "open_price": -10.50,  # 负价格
            "high_price": 11.00,
            "low_price": 10.20,
            "close_price": 10.80,
            "volume": -1000,  # 负成交量
            "amount": 10800000.0,
        }

        result = composite.validate(invalid_data)
        assert not result.is_valid
        assert len(result.errors) >= 2

    def test_composite_validator_batch_validation(self, validation_config):
        """测试批量验证集成"""
        validators = [PriceValidator(validation_config), VolumeValidator(validation_config)]
        composite = CompositeValidator(validators)

        data_list = [
            {
                "stock_code": "000001",
                "open_price": 10.0,
                "high_price": 11.0,
                "low_price": 10.0,
                "close_price": 10.5,
                "volume": 1000000,
                "amount": 10000000.0,
            },
            {
                "stock_code": "000002",
                "open_price": 20.0,
                "high_price": 21.0,
                "low_price": 20.0,
                "close_price": 20.5,
                "volume": 2000000,
                "amount": 20000000.0,
            },
            {
                "stock_code": "000003",
                "open_price": -5.0,  # 无效数据
                "high_price": 0,
                "low_price": 0,
                "close_price": 0,
                "volume": 0,
                "amount": 0,
            },
        ]

        results = composite.validate_batch(data_list)
        assert len(results) == 3
        assert results[0].is_valid
        assert results[1].is_valid
        assert not results[2].is_valid

    def test_config_strict_mode(self):
        """测试严格模式配置"""
        config = ValidationConfig()
        config.STRICT_MODE = True

        assert config.STRICT_MODE is True

    def test_config_auto_clean(self):
        """测试自动清洗配置"""
        config = ValidationConfig()
        config.AUTO_CLEAN = True

        assert config.AUTO_CLEAN is True

    def test_default_config_values(self):
        """测试默认配置值"""
        config = ValidationConfig()

        assert config.MIN_PRICE == 0.01
        assert config.MAX_PRICE == 10000
        assert config.MIN_VOLUME == 0
        assert config.MAX_VOLUME == 1000000000000
        assert config.MIN_AMOUNT == 0
        assert config.MAX_AMOUNT == 100000000000000
        assert config.MAX_CHANGE_PCT == 20.0
        assert config.PRICE_CHANGE_TOLERANCE == 0.5
        assert config.STRICT_MODE is False
        assert config.AUTO_CLEAN is True

    def test_global_config(self):
        """测试全局配置对象"""
        assert hasattr(config, "validation")
        assert isinstance(config.validation, ValidationConfig)

    def test_price_validator_without_config(self):
        """测试价格验证器不传递配置时使用默认配置"""
        validator = PriceValidator()

        data = {
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 10.0,
            "close_price": 10.5,
        }

        result = validator.validate(data)
        assert result.is_valid

    def test_volume_validator_without_config(self):
        """测试成交量验证器不传递配置时使用默认配置"""
        validator = VolumeValidator()

        data = {
            "volume": 1000000,
            "amount": 10000000.0,
            "close_price": 10.0,
        }

        result = validator.validate(data)
        assert result.is_valid


class TestValidationEdgeCases:
    """验证边界情况"""

    def test_nan_values(self, validation_config):
        """测试 NaN 值处理"""
        validator = PriceValidator(validation_config)

        data = {
            "open_price": float("nan"),
            "high_price": 10.0,
            "low_price": 9.0,
            "close_price": 10.0,
        }

        result = validator.validate(data)
        assert not result.is_valid
        assert any("NaN" in error for error in result.errors)

    def test_infinite_values(self, validation_config):
        """测试无穷大值处理"""
        validator = PriceValidator(validation_config)

        data = {
            "open_price": float("inf"),
            "high_price": 10.0,
            "low_price": 9.0,
            "close_price": 10.0,
        }

        result = validator.validate(data)
        assert not result.is_valid
        assert any("infinite" in error for error in result.errors)

    def test_zero_prices(self, validation_config):
        """测试零价格处理"""
        validator = PriceValidator(validation_config)

        data = {
            "open_price": 0.0,
            "high_price": 0.0,
            "low_price": 0.0,
            "close_price": 0.0,
        }

        result = validator.validate(data)
        assert not result.is_valid
        assert any("为零" in error for error in result.errors)

    def test_ohlc_logic_error(self, validation_config):
        """测试 OHLC 逻辑错误"""
        validator = PriceValidator(validation_config)

        # 最高价小于最低价
        data = {
            "open_price": 10.0,
            "high_price": 9.0,
            "low_price": 10.0,
            "close_price": 9.5,
        }

        result = validator.validate(data)
        assert not result.is_valid
        assert any("OHLC" in error or "逻辑" in error for error in result.errors)

    def test_close_out_of_range(self, validation_config):
        """测试收盘价超出最高最低价范围"""
        validator = PriceValidator(validation_config)

        # 收盘价高于最高价
        data = {
            "open_price": 10.0,
            "high_price": 11.0,
            "low_price": 9.0,
            "close_price": 12.0,
        }

        result = validator.validate(data)
        assert not result.is_valid

    def test_volume_amount_mismatch(self, validation_config):
        """测试成交额与成交量不匹配"""
        validator = VolumeValidator(validation_config)

        data = {
            "volume": 1000000,
            "amount": 100.0,  # 成交额远小于预期
            "close_price": 10.0,
        }

        result = validator.validate(data)
        assert not result.is_valid
        assert any("不匹配" in error for error in result.errors)
