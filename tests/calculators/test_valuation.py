"""ValuationCalculator 估值指标计算器单元测试"""

import pytest

from ecox.calculators.valuation import ValuationCalculator


class TestValuationCalculator:
    """测试 ValuationCalculator 类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return ValuationCalculator()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "profit_sheet": {"net_profit": 150000, "total_revenue": 1000000},
            "balance_sheet": {"owner_equity": 3000000},
            "cash_flow_sheet": {},
            "market_data": {
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": 300000,
                "earnings_growth": 0.20,
            },
        }

    def test_calculate_pe_ratio(self, calculator, sample_data):
        """测试市盈率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
            market_data=sample_data["market_data"],
        )
        # PE = 5000000 / 150000 = 33.3333
        assert result["pe_ratio"] == 33.3333

    def test_calculate_pb_ratio(self, calculator, sample_data):
        """测试市净率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
            market_data=sample_data["market_data"],
        )
        # PB = 5000000 / 3000000 = 1.6667
        assert result["pb_ratio"] == 1.6667

    def test_calculate_ps_ratio(self, calculator, sample_data):
        """测试市销率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
            market_data=sample_data["market_data"],
        )
        # PS = 5000000 / 1000000 = 5.0
        assert result["ps_ratio"] == 5.0

    def test_calculate_ev_ebitda(self, calculator, sample_data):
        """测试 EV/EBITDA 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
            market_data=sample_data["market_data"],
        )
        # EV = 5000000 + 2000000 - 500000 = 6500000
        # EV/EBITDA = 6500000 / 300000 = 21.6667
        assert result["ev_ebitda"] == 21.6667

    def test_calculate_peg_ratio(self, calculator, sample_data):
        """测试 PEG 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
            market_data=sample_data["market_data"],
        )
        # PE = 33.3333
        # PEG = 33.3333 / (0.20 * 100) = 1.6667
        assert result["peg_ratio"] == 1.6667

    def test_calculate_with_missing_market_data(self, calculator):
        """测试缺失市场数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "total_revenue": 1000000},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data=None,
        )
        assert result["pe_ratio"] is None
        assert result["pb_ratio"] is None
        assert result["ps_ratio"] is None
        assert result["ev_ebitda"] is None
        assert result["peg_ratio"] is None

    def test_calculate_with_empty_market_data(self, calculator):
        """测试空市场数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "total_revenue": 1000000},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data={},
        )
        assert result["pe_ratio"] is None
        assert result["pb_ratio"] is None
        assert result["ps_ratio"] is None
        assert result["ev_ebitda"] is None
        assert result["peg_ratio"] is None

    def test_calculate_with_missing_profit_sheet_data(self, calculator):
        """测试缺失利润表数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": 300000,
                "earnings_growth": 0.20,
            },
        )
        assert result["pe_ratio"] is None
        assert result["ps_ratio"] is None
        # PB 不依赖利润表
        assert result["pb_ratio"] == 1.6667

    def test_calculate_with_missing_balance_sheet_data(self, calculator):
        """测试缺失资产负债表数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "total_revenue": 1000000},
            balance_sheet={},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": 300000,
                "earnings_growth": 0.20,
            },
        )
        assert result["pb_ratio"] is None
        # PE 不依赖资产负债表
        assert result["pe_ratio"] == 33.3333

    def test_calculate_with_zero_divisor(self, calculator):
        """测试除数为零时返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 0, "total_revenue": 0},
            balance_sheet={"owner_equity": 0},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": 0,
                "earnings_growth": 0,
            },
        )
        # 除数为零时应该返回 None
        assert result["pe_ratio"] is None
        assert result["pb_ratio"] is None
        assert result["ps_ratio"] is None
        assert result["ev_ebitda"] is None
        assert result["peg_ratio"] is None

    def test_calculate_with_negative_profit(self, calculator):
        """测试负利润情况（亏损公司）"""
        result = calculator.calculate(
            profit_sheet={"net_profit": -100000, "total_revenue": 1000000},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": 300000,
                "earnings_growth": -0.10,
            },
        )
        # 负利润时 PE 为负值
        assert result["pe_ratio"] == -50.0  # 5000000 / -100000
        # 负增长率时 PEG 为正值（负负得正）
        # PE = -50, 增长率 = -0.10 * 100 = -10
        # PEG = -50 / -10 = 5.0
        assert result["peg_ratio"] == 5.0

    def test_calculate_with_missing_ebitda(self, calculator):
        """测试缺失 EBITDA 时 ev_ebitda 返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "total_revenue": 1000000},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": None,
                "earnings_growth": 0.20,
            },
        )
        assert result["ev_ebitda"] is None
        # 其他指标应该正常计算
        assert result["pe_ratio"] == 33.3333
        assert result["pb_ratio"] == 1.6667

    def test_calculate_with_missing_earnings_growth(self, calculator):
        """测试缺失增长率时 peg_ratio 返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "total_revenue": 1000000},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                "total_debt": 2000000,
                "cash": 500000,
                "ebitda": 300000,
                "earnings_growth": None,
            },
        )
        assert result["peg_ratio"] is None
        # 其他指标应该正常计算
        assert result["pe_ratio"] == 33.3333
        assert result["pb_ratio"] == 1.6667

    def test_calculate_with_partial_market_data(self, calculator):
        """测试部分市场数据缺失"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "total_revenue": 1000000},
            balance_sheet={"owner_equity": 3000000},
            cash_flow_sheet={},
            market_data={
                "market_cap": 5000000,
                # 缺失 total_debt 和 cash
                "ebitda": 300000,
                "earnings_growth": 0.20,
            },
        )
        # PE 和 PB 应该正常计算
        assert result["pe_ratio"] == 33.3333
        assert result["pb_ratio"] == 1.6667
        # EV/EBITDA 缺失债务和现金数据，使用默认值 0
        # EV = 5000000 + 0 - 0 = 5000000
        # EV/EBITDA = 5000000 / 300000 = 16.6667
        assert result["ev_ebitda"] == 16.6667
