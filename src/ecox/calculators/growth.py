"""成长能力计算器"""

import math
from typing import Any

from ecox.calculators.base import BaseCalculator


class GrowthCalculator(BaseCalculator):
    """成长能力计算器

    计算企业的成长能力相关指标，包括收入增长率、利润增长率
    和各类复合增长率。
    """

    @staticmethod
    def _calculate_cagr(end_value: float | None, start_value: float | None, years: int) -> float | None:
        """计算复合年增长率 (CAGR)

        CAGR = (end_value / start_value) ^ (1 / years) - 1

        Args:
            end_value: 期末值
            start_value: 期初值（必须为正数）
            years: 年数

        Returns:
            复合年增长率，如果无法计算则返回 None
        """
        if end_value is None or start_value is None:
            return None
        if start_value <= 0 or years <= 0:
            return None
        try:
            ratio = end_value / start_value
            cagr = math.pow(ratio, 1 / years) - 1
            return round(cagr, 4)
        except (ValueError, ZeroDivisionError, OverflowError):
            return None

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """计算成长能力指标

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（可选）

        Returns:
            包含以下指标的字典:
            - revenue_growth_1y: 收入增长率(1年) = (本期营收 - 上期营收) / 上期营收
            - profit_growth_1y: 利润增长率(1年) = (本期利润 - 上期利润) / 上期利润
            - revenue_cagr_5y: 收入5年复合增长率
            - profit_cagr_5y: 利润5年复合增长率
            - fcff_cagr_5y: FCF 5年复合增长率
        """
        # 提取利润表数据
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        prev_total_revenue = self._safe_float(profit_sheet.get("prev_total_revenue"))
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        prev_net_profit = self._safe_float(profit_sheet.get("prev_net_profit"))
        revenue_history = profit_sheet.get("revenue_history", [])
        profit_history = profit_sheet.get("profit_history", [])
        fcff_history = profit_sheet.get("fcff_history", [])

        # 计算收入增长率(1年)
        revenue_growth_1y = None
        if total_revenue is not None and prev_total_revenue is not None and prev_total_revenue != 0:
            revenue_growth_1y = self._round((total_revenue - prev_total_revenue) / prev_total_revenue)

        # 计算利润增长率(1年)
        profit_growth_1y = None
        if net_profit is not None and prev_net_profit is not None and prev_net_profit != 0:
            profit_growth_1y = self._round((net_profit - prev_net_profit) / prev_net_profit)

        # 计算5年复合增长率（需要至少5个数据点）
        revenue_cagr_5y = None
        if len(revenue_history) >= 5:
            start_value = self._safe_float(revenue_history[0])
            end_value = self._safe_float(revenue_history[-1])
            # 5个数据点代表4年的增长
            revenue_cagr_5y = self._calculate_cagr(end_value, start_value, 4)

        profit_cagr_5y = None
        if len(profit_history) >= 5:
            start_value = self._safe_float(profit_history[0])
            end_value = self._safe_float(profit_history[-1])
            profit_cagr_5y = self._calculate_cagr(end_value, start_value, 4)

        fcff_cagr_5y = None
        if len(fcff_history) >= 5:
            start_value = self._safe_float(fcff_history[0])
            end_value = self._safe_float(fcff_history[-1])
            fcff_cagr_5y = self._calculate_cagr(end_value, start_value, 4)

        return {
            "revenue_growth_1y": revenue_growth_1y,
            "profit_growth_1y": profit_growth_1y,
            "revenue_cagr_5y": revenue_cagr_5y,
            "profit_cagr_5y": profit_cagr_5y,
            "fcff_cagr_5y": fcff_cagr_5y,
        }
