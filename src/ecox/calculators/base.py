"""计算器基类"""

import math
from abc import ABC, abstractmethod
from typing import Any


class BaseCalculator(ABC):
    """计算器基类

    所有财务指标计算器的抽象基类，提供通用的工具方法。
    """

    @staticmethod
    def _round(value: float | None) -> float | None:
        """保留4位小数，处理 None、NaN、Inf

        Args:
            value: 需要四舍五入的值

        Returns:
            保留4位小数的浮点数，如果输入为 None、NaN 或 Inf 则返回 None
        """
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return round(float_val, 4)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """安全转换为浮点数，处理 None、NaN、Inf、无效字符串

        Args:
            value: 需要转换的值

        Returns:
            转换后的浮点数，如果转换失败、输入为 None、NaN 或 Inf 则返回 None
        """
        if value is None:
            return None
        try:
            result = float(value)
            if math.isnan(result) or math.isinf(result):
                return None
            return result
        except (ValueError, TypeError):
            return None

    @abstractmethod
    def calculate(
        self,
        profit_sheet: dict,
        balance_sheet: dict,
        cash_flow_sheet: dict,
        market_data: dict | None = None,
    ) -> dict:
        """计算财务指标

        子类必须实现此方法来计算具体的财务指标。

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（可选），如股价、市值等

        Returns:
            包含计算结果的字典
        """
        pass
