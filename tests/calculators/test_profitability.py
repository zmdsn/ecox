"""ProfitabilityCalculator 盈利能力计算器单元测试"""

import pytest

from ecox.calculators.profitability import ProfitabilityCalculator


class TestProfitabilityCalculator:
    """测试 ProfitabilityCalculator 类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return ProfitabilityCalculator()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "operating_profit": 200000,
                "net_profit": 150000,
                "operating_cost": 400000,
            },
            "balance_sheet": {
                "total_assets": 5000000,
                "owner_equity": 3000000,
                "total_liabilities": 2000000,
            },
            "cash_flow_sheet": {},
        }

    def test_calculate_roe(self, calculator, sample_data):
        """测试 ROE 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # ROE = 150000 / 3000000 = 0.05
        assert result["roe"] == 0.0500

    def test_calculate_roa(self, calculator, sample_data):
        """测试 ROA 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # ROA = 150000 / 5000000 = 0.03
        assert result["roa"] == 0.0300

    def test_calculate_roic(self, calculator, sample_data):
        """测试 ROIC 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # ROIC = 150000 / (3000000 + 2000000) = 0.03
        assert result["roic"] == 0.0300

    def test_calculate_gross_margin(self, calculator, sample_data):
        """测试毛利率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # 毛利率 = (1000000 - 400000) / 1000000 = 0.6
        assert result["gross_margin"] == 0.6000

    def test_calculate_net_margin(self, calculator, sample_data):
        """测试净利率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # 净利率 = 150000 / 1000000 = 0.15
        assert result["net_margin"] == 0.1500

    def test_calculate_operating_margin(self, calculator, sample_data):
        """测试营业利润率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # 营业利润率 = 200000 / 1000000 = 0.2
        assert result["operating_margin"] == 0.2000

    def test_calculate_with_missing_data(self, calculator):
        """测试缺失数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["roe"] is None
        assert result["roa"] is None
        assert result["roic"] is None
        assert result["gross_margin"] is None
        assert result["net_margin"] is None
        assert result["operating_margin"] is None

    def test_calculate_with_zero_divisor(self, calculator):
        """测试除数为零时返回 None"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 0,
                "operating_profit": 200000,
                "net_profit": 150000,
                "operating_cost": 400000,
            },
            balance_sheet={
                "total_assets": 0,
                "owner_equity": 0,
                "total_liabilities": 0,
            },
            cash_flow_sheet={},
        )
        # 除数为零时应该返回 None
        assert result["roe"] is None
        assert result["roa"] is None
        assert result["roic"] is None
        assert result["gross_margin"] is None
        assert result["net_margin"] is None
        assert result["operating_margin"] is None

    def test_calculate_with_negative_values(self, calculator):
        """测试负值计算（亏损情况）"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 1000000,
                "operating_profit": -100000,
                "net_profit": -50000,
                "operating_cost": 800000,
            },
            balance_sheet={
                "total_assets": 5000000,
                "owner_equity": 3000000,
                "total_liabilities": 2000000,
            },
            cash_flow_sheet={},
        )
        # 负值应该正常计算
        assert result["roe"] == -0.0167  # -50000 / 3000000
        assert result["roa"] == -0.0100  # -50000 / 5000000
        assert result["net_margin"] == -0.0500  # -50000 / 1000000
