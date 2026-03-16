"""估值指标计算器"""

from typing import Any

from ecox.calculators.base import BaseCalculator


class ValuationCalculator(BaseCalculator):
    """估值指标计算器

    计算企业的估值相关指标，包括 PE、PB、PS、EV/EBITDA、PEG。
    """

    def calculate(
        self,
        profit_sheet: dict[str, Any],
        balance_sheet: dict[str, Any],
        cash_flow_sheet: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """计算估值指标

        Args:
            profit_sheet: 利润表数据
            balance_sheet: 资产负债表数据
            cash_flow_sheet: 现金流量表数据
            market_data: 市场数据（必需），包括市值、债务、现金等

        Returns:
            包含以下指标的字典:
            - pe_ratio: 市盈率 = 市值 / 净利润
            - pb_ratio: 市净率 = 市值 / 净资产
            - ps_ratio: 市销率 = 市值 / 营收
            - ev_ebitda: EV/EBITDA = (市值 + 债务 - 现金) / EBITDA
            - peg_ratio: PEG = PE / (增长率 * 100)
        """
        # 如果没有市场数据，所有指标返回 None
        if market_data is None:
            return {
                "pe_ratio": None,
                "pb_ratio": None,
                "ps_ratio": None,
                "ev_ebitda": None,
                "peg_ratio": None,
            }

        # 提取利润表数据
        net_profit = self._safe_float(profit_sheet.get("net_profit"))
        total_revenue = self._safe_float(profit_sheet.get("total_revenue"))

        # 提取资产负债表数据
        owner_equity = self._safe_float(balance_sheet.get("owner_equity"))

        # 提取市场数据
        market_cap = self._safe_float(market_data.get("market_cap"))
        total_debt = self._safe_float(market_data.get("total_debt")) or 0.0
        cash = self._safe_float(market_data.get("cash")) or 0.0
        ebitda = self._safe_float(market_data.get("ebitda"))
        earnings_growth = self._safe_float(market_data.get("earnings_growth"))

        # 计算市盈率: PE = 市值 / 净利润
        pe_ratio = None
        if market_cap is not None and net_profit is not None and net_profit != 0:
            pe_ratio = self._round(market_cap / net_profit)

        # 计算市净率: PB = 市值 / 净资产
        pb_ratio = None
        if market_cap is not None and owner_equity is not None and owner_equity != 0:
            pb_ratio = self._round(market_cap / owner_equity)

        # 计算市销率: PS = 市值 / 营收
        ps_ratio = None
        if market_cap is not None and total_revenue is not None and total_revenue != 0:
            ps_ratio = self._round(market_cap / total_revenue)

        # 计算 EV/EBITDA: EV = 市值 + 债务 - 现金
        ev_ebitda = None
        if (
            market_cap is not None
            and total_debt is not None
            and cash is not None
            and ebitda is not None
            and ebitda != 0
        ):
            ev = market_cap + total_debt - cash
            ev_ebitda = self._round(ev / ebitda)

        # 计算 PEG: PEG = PE / (增长率 * 100)
        peg_ratio = None
        if (
            pe_ratio is not None
            and earnings_growth is not None
            and earnings_growth != 0
        ):
            growth_rate = earnings_growth * 100
            peg_ratio = self._round(pe_ratio / growth_rate)

        return {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "ps_ratio": ps_ratio,
            "ev_ebitda": ev_ebitda,
            "peg_ratio": peg_ratio,
        }
