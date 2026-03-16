"""CashFlowCalculator 现金流分析计算器单元测试"""

import pytest

from ecox.calculators.cash_flow import CashFlowCalculator


class TestCashFlowCalculator:
    """测试 CashFlowCalculator 类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return CashFlowCalculator()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "net_profit": 150000,
                "interest_expense": 10000,
            },
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 200000,
                "capex": 50000,
            },
        }

    def test_calculate_fcff(self, calculator, sample_data):
        """测试 FCFF 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # FCFF = 200000 - 50000 = 150000
        assert result["fcff"] == 150000.0000

    def test_calculate_fcfe(self, calculator, sample_data):
        """测试 FCFE 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # FCFE = 150000 - 10000 = 140000
        assert result["fcfe"] == 140000.0000

    def test_calculate_capex(self, calculator, sample_data):
        """测试 CAPEX 返回"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        assert result["capex"] == 50000.0000

    def test_calculate_cash_conversion_rate(self, calculator, sample_data):
        """测试现金转换率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # 现金转换率 = 150000 / 150000 = 1.0
        assert result["cash_conversion_rate"] == 1.0000

    def test_calculate_ocf_to_sales(self, calculator, sample_data):
        """测试 OCF/营收 计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # OCF/营收 = 200000 / 1000000 = 0.2
        assert result["ocf_to_sales"] == 0.2000

    def test_calculate_with_negative_fcff(self, calculator):
        """测试负 FCFF 情况"""
        data = {
            "profit_sheet": {"total_revenue": 1000000, "net_profit": 150000},
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 30000,
                "capex": 100000,
            },
        }
        result = calculator.calculate(
            profit_sheet=data["profit_sheet"],
            balance_sheet=data["balance_sheet"],
            cash_flow_sheet=data["cash_flow_sheet"],
        )
        # FCFF = 30000 - 100000 = -70000
        assert result["fcff"] == -70000.0000

    def test_calculate_with_missing_data(self, calculator):
        """测试缺失数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["fcff"] is None
        assert result["fcfe"] is None
        assert result["capex"] is None
        assert result["cash_conversion_rate"] is None
        assert result["ocf_to_sales"] is None

    def test_calculate_with_zero_net_profit(self, calculator):
        """测试净利润为零时现金转换率返回 None"""
        data = {
            "profit_sheet": {
                "total_revenue": 1000000,
                "net_profit": 0,
                "interest_expense": 10000,
            },
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 200000,
                "capex": 50000,
            },
        }
        result = calculator.calculate(
            profit_sheet=data["profit_sheet"],
            balance_sheet=data["balance_sheet"],
            cash_flow_sheet=data["cash_flow_sheet"],
        )
        # 除数为零时应该返回 None
        assert result["cash_conversion_rate"] is None
        # 其他指标应正常计算
        assert result["fcff"] == 150000.0000

    def test_calculate_with_zero_revenue(self, calculator):
        """测试营业收入为零时 OCF/营收 返回 None"""
        data = {
            "profit_sheet": {
                "total_revenue": 0,
                "net_profit": 150000,
                "interest_expense": 10000,
            },
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 200000,
                "capex": 50000,
            },
        }
        result = calculator.calculate(
            profit_sheet=data["profit_sheet"],
            balance_sheet=data["balance_sheet"],
            cash_flow_sheet=data["cash_flow_sheet"],
        )
        # 除数为零时应该返回 None
        assert result["ocf_to_sales"] is None
        # 其他指标应正常计算
        assert result["fcff"] == 150000.0000

    def test_calculate_fcfe_without_interest_expense(self, calculator):
        """测试无利息支出时 FCFE 等于 FCFF"""
        data = {
            "profit_sheet": {
                "total_revenue": 1000000,
                "net_profit": 150000,
                # 无 interest_expense
            },
            "balance_sheet": {},
            "cash_flow_sheet": {
                "operating_cash_flow": 200000,
                "capex": 50000,
            },
        }
        result = calculator.calculate(
            profit_sheet=data["profit_sheet"],
            balance_sheet=data["balance_sheet"],
            cash_flow_sheet=data["cash_flow_sheet"],
        )
        # FCFE = FCFF = 150000 (无利息支出)
        assert result["fcff"] == 150000.0000
        assert result["fcfe"] == 150000.0000
