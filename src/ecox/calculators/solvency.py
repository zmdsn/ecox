"""偿债能力计算器"""

from typing import Any

from ecox.calculators.base import BaseCalculator


class SolvencyCalculator(BaseCalculator):
    """偿债能力计算器

    计算企业的偿债能力相关指标，包括资产负债率、流动比率、
    速动比率和利息保障倍数。
    """

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """计算偿债能力指标

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（可选）

        Returns:
            包含以下指标的字典:
            - debt_ratio: 资产负债率 = 总负债 / 总资产
            - current_ratio: 流动比率 = 流动资产 / 流动负债
            - quick_ratio: 速动比率 = (流动资产 - 存货) / 流动负债
            - interest_coverage: 利息保障倍数 = 营业利润 / 利息支出
        """
        # 提取资产负债表数据
        total_assets = self._safe_float(balance_sheet.get("total_assets"))
        total_liabilities = self._safe_float(balance_sheet.get("total_liabilities"))
        current_assets = self._safe_float(balance_sheet.get("current_assets"))
        current_liabilities = self._safe_float(balance_sheet.get("current_liabilities"))
        inventory = self._safe_float(balance_sheet.get("inventory"))

        # 提取利润表数据
        operating_profit = self._safe_float(profit_sheet.get("operating_profit"))
        interest_expense = self._safe_float(profit_sheet.get("interest_expense"))

        # 计算资产负债率: 总负债 / 总资产
        debt_ratio = None
        if total_liabilities is not None and total_assets is not None and total_assets != 0:
            debt_ratio = self._round(total_liabilities / total_assets)

        # 计算流动比率: 流动资产 / 流动负债
        current_ratio = None
        if current_assets is not None and current_liabilities is not None and current_liabilities != 0:
            current_ratio = self._round(current_assets / current_liabilities)

        # 计算速动比率: (流动资产 - 存货) / 流动负债
        quick_ratio = None
        if (
            current_assets is not None
            and inventory is not None
            and current_liabilities is not None
            and current_liabilities != 0
        ):
            quick_ratio = self._round((current_assets - inventory) / current_liabilities)

        # 计算利息保障倍数: 营业利润 / 利息支出
        interest_coverage = None
        if operating_profit is not None and interest_expense is not None and interest_expense != 0:
            interest_coverage = self._round(operating_profit / interest_expense)

        return {
            "debt_ratio": debt_ratio,
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "interest_coverage": interest_coverage,
        }
