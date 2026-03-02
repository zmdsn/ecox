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
            result.add_error(f"Close price is negative: {close}")
        if open_price < 0:
            result.add_error(f"Open price is negative: {open_price}")
        if high < 0:
            result.add_error(f"High price is negative: {high}")
        if low < 0:
            result.add_error(f"Low price is negative: {low}")

        # 检查价格范围
        if close > 0 and (close < self.MIN_PRICE or close > self.MAX_PRICE):
            result.add_error(f"Close price out of range: {close}")
        if open_price > 0 and (open_price < self.MIN_PRICE or open_price > self.MAX_PRICE):
            result.add_error(f"Open price out of range: {open_price}")

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
