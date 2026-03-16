"""盈利能力计算器"""

from typing import Any

from ecox.calculators.base import BaseCalculator


class ProfitabilityCalculator(BaseCalculator):
    """盈利能力计算器

    计算企业的盈利能力相关指标，包括 ROE、ROA、ROIC、
    毛利率、净利率和营业利润率。
    """

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """计算盈利能力指标

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（可选）

        Returns:
            包含以下指标的字典:
            - roe: 净资产收益率 = 净利润 / 所有者权益
            - roa: 总资产收益率 = 净利润 / 总资产
            - roic: 投入资本回报率 = 净利润 / (所有者权益 + 有息负债)
                   （简化版：假设有息负债=总负债）
            - gross_margin: 毛利率 = (营收 - 营业成本) / 营收
            - net_margin: 净利率 = 净利润 / 营收
            - operating_margin: 营业利润率 = 营业利润 / 营收
        """
        # 提取利润表数据
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))
        operating_profit = self._safe_float(profit_sheet.get("operating_profit"))
        operating_cost = self._safe_float(profit_sheet.get("operating_cost"))

        # 提取资产负债表数据
        total_assets = self._safe_float(balance_sheet.get("total_assets"))
        owner_equity = self._safe_float(balance_sheet.get("owner_equity"))
        total_liabilities = self._safe_float(balance_sheet.get("total_liabilities"))

        # 计算 ROE: 净资产收益率 = 净利润 / 所有者权益
        roe = None
        if net_profit is not None and owner_equity is not None and owner_equity != 0:
            roe = self._round(net_profit / owner_equity)

        # 计算 ROA: 总资产收益率 = 净利润 / 总资产
        roa = None
        if net_profit is not None and total_assets is not None and total_assets != 0:
            roa = self._round(net_profit / total_assets)

        # 计算 ROIC: 投入资本回报率 = 净利润 / (所有者权益 + 有息负债)
        # 简化版：假设有息负债 = 总负债
        roic = None
        if net_profit is not None and owner_equity is not None and total_liabilities is not None:
            invested_capital = owner_equity + total_liabilities
            if invested_capital != 0:
                roic = self._round(net_profit / invested_capital)

        # 计算毛利率: (营收 - 营业成本) / 营收
        gross_margin = None
        if total_revenue is not None and operating_cost is not None and total_revenue != 0:
            gross_margin = self._round((total_revenue - operating_cost) / total_revenue)

        # 计算净利率: 净利润 / 营收
        net_margin = None
        if net_profit is not None and total_revenue is not None and total_revenue != 0:
            net_margin = self._round(net_profit / total_revenue)

        # 计算营业利润率: 营业利润 / 营收
        operating_margin = None
        if operating_profit is not None and total_revenue is not None and total_revenue != 0:
            operating_margin = self._round(operating_profit / total_revenue)

        return {
            "roe": roe,
            "roa": roa,
            "roic": roic,
            "gross_margin": gross_margin,
            "net_margin": net_margin,
            "operating_margin": operating_margin,
        }
