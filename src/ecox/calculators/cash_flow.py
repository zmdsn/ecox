"""现金流分析计算器"""

from typing import Any

from ecox.calculators.base import BaseCalculator


class CashFlowCalculator(BaseCalculator):
    """现金流分析计算器

    计算企业的现金流相关指标，包括 FCFF、FCFE、CAPEX、
    现金转换率和 OCF/营收。
    """

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """计算现金流分析指标

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（可选）

        Returns:
            包含以下指标的字典:
            - fcff: 企业自由现金流 = 经营现金流 - 资本支出
            - fcfe: 股权自由现金流 = FCFF - 利息支出（简化版）
            - capex: 资本支出（直接返回）
            - cash_conversion_rate: 现金转换率 = FCFF / 净利润
            - ocf_to_sales: 经营现金流 / 营业收入
        """
        # 提取现金流量表数据
        operating_cash_flow = self._safe_float(cash_flow_sheet.get("operating_cash_flow"))
        capex = self._safe_float(cash_flow_sheet.get("capex"))

        # 提取利润表数据
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        interest_expense = self._safe_float(profit_sheet.get("interest_expense"))

        # 计算 FCFF: 企业自由现金流 = 经营现金流 - 资本支出
        fcff = None
        if operating_cash_flow is not None and capex is not None:
            fcff = self._round(operating_cash_flow - capex)

        # 计算 FCFE: 股权自由现金流 = FCFF - 利息支出（简化版）
        fcfe = None
        if fcff is not None:
            if interest_expense is not None:
                fcfe = self._round(fcff - interest_expense)
            else:
                # 无利息支出时，FCFE = FCFF
                fcfe = self._round(fcff)

        # CAPEX: 资本支出（直接返回）
        capex_result = self._round(capex) if capex is not None else None

        # 计算现金转换率: FCFF / 净利润
        cash_conversion_rate = None
        if fcff is not None and net_profit is not None and net_profit != 0:
            cash_conversion_rate = self._round(fcff / net_profit)

        # 计算 OCF/营收: 经营现金流 / 营业收入
        ocf_to_sales = None
        if operating_cash_flow is not None and total_revenue is not None and total_revenue != 0:
            ocf_to_sales = self._round(operating_cash_flow / total_revenue)

        return {
            "fcff": fcff,
            "fcfe": fcfe,
            "capex": capex_result,
            "cash_conversion_rate": cash_conversion_rate,
            "ocf_to_sales": ocf_to_sales,
        }
