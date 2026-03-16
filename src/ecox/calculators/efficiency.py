"""营运能力计算器"""

from typing import Any

from ecox.calculators.base import BaseCalculator


class EfficiencyCalculator(BaseCalculator):
    """营运能力计算器

    计算企业的营运能力相关指标，包括存货周转率、应收账款周转率和总资产周转率。
    """

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """计算营运能力指标

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（可选）

        Returns:
            包含以下指标的字典:
            - inventory_turnover: 存货周转率 = 营业成本 / 存货
            - receivables_turnover: 应收账款周转率 = 营收 / 应收账款
            - asset_turnover: 总资产周转率 = 营收 / 总资产
        """
        # 提取利润表数据
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        operating_cost = self._safe_float(profit_sheet.get("operating_cost"))

        # 提取资产负债表数据
        total_assets = self._safe_float(balance_sheet.get("total_assets"))
        inventory = self._safe_float(balance_sheet.get("inventory"))
        accounts_receivable = self._safe_float(balance_sheet.get("accounts_receivable"))

        # 计算存货周转率: 营业成本 / 存货
        inventory_turnover = None
        if operating_cost is not None and inventory is not None and inventory != 0:
            inventory_turnover = self._round(operating_cost / inventory)

        # 计算应收账款周转率: 营收 / 应收账款
        receivables_turnover = None
        if total_revenue is not None and accounts_receivable is not None and accounts_receivable != 0:
            receivables_turnover = self._round(total_revenue / accounts_receivable)

        # 计算总资产周转率: 营收 / 总资产
        asset_turnover = None
        if total_revenue is not None and total_assets is not None and total_assets != 0:
            asset_turnover = self._round(total_revenue / total_assets)

        return {
            "inventory_turnover": inventory_turnover,
            "receivables_turnover": receivables_turnover,
            "asset_turnover": asset_turnover,
        }
