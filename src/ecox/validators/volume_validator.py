"""成交量验证器"""
from typing import Dict, Any
import math

from .base import DataValidator
from .result import ValidationResult


class VolumeValidator(DataValidator):
    """成交量验证器

    验证规则：
    1. 成交量必须非负
    2. 成交额必须非负
    3. 成交额应该 >= 成交量 * 最低价（粗略检查）
    """

    def __init__(self, config=None):
        """初始化成交量验证器

        Args:
            config: 验证配置对象，如果为None则使用默认配置
        """
        if config is None:
            from ecox.config import VALIDATION_CONFIG
            config = VALIDATION_CONFIG

        self.config = config

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
                elif volume > self.config.MAX_VOLUME:
                    result.add_error(f"成交量超过最大值: {volume}")
            except (ValueError, TypeError):
                result.add_error(f"成交量格式错误: {volume}")

        # 检查成交额
        if amount is not None:
            try:
                amount = float(amount)
                if amount < 0:
                    result.add_error(f"成交额为负: {amount}")
                elif amount > self.config.MAX_AMOUNT:
                    result.add_error(f"成交额超过最大值: {amount}")

                # 检查成交额与成交量的合理性
                if volume and amount > 0 and close > 0 and not math.isnan(close):
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
