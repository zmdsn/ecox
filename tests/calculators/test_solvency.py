"""SolvencyCalculator 偿债能力计算器单元测试"""

import pytest

from ecox.calculators.solvency import SolvencyCalculator


class TestSolvencyCalculator:
    """测试 SolvencyCalculator 类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return SolvencyCalculator()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "profit_sheet": {"operating_profit": 200000, "interest_expense": 10000},
            "balance_sheet": {
                "total_assets": 5000000,
                "total_liabilities": 2000000,
                "current_assets": 1500000,
                "current_liabilities": 800000,
                "inventory": 300000,
                "owner_equity": 3000000,
            },
            "cash_flow_sheet": {},
        }

    def test_calculate_debt_ratio(self, calculator, sample_data):
        """测试资产负债率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # debt_ratio = 2000000 / 5000000 = 0.4
        assert result["debt_ratio"] == 0.4000

    def test_calculate_current_ratio(self, calculator, sample_data):
        """测试流动比率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # current_ratio = 1500000 / 800000 = 1.875
        assert result["current_ratio"] == 1.8750

    def test_calculate_quick_ratio(self, calculator, sample_data):
        """测试速动比率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # quick_ratio = (1500000 - 300000) / 800000 = 1.5
        assert result["quick_ratio"] == 1.5000

    def test_calculate_interest_coverage(self, calculator, sample_data):
        """测试利息保障倍数计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # interest_coverage = 200000 / 10000 = 20
        assert result["interest_coverage"] == 20.0000

    def test_calculate_with_missing_data(self, calculator):
        """测试缺失数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["debt_ratio"] is None
        assert result["current_ratio"] is None
        assert result["quick_ratio"] is None
        assert result["interest_coverage"] is None

    def test_calculate_with_zero_divisor(self, calculator):
        """测试除数为零时返回 None"""
        result = calculator.calculate(
            profit_sheet={"operating_profit": 200000, "interest_expense": 0},
            balance_sheet={
                "total_assets": 0,
                "total_liabilities": 0,
                "current_assets": 0,
                "current_liabilities": 0,
                "inventory": 0,
                "owner_equity": 0,
            },
            cash_flow_sheet={},
        )
        # 除数为零时应该返回 None
        assert result["debt_ratio"] is None
        assert result["current_ratio"] is None
        assert result["quick_ratio"] is None
        # interest_coverage 分母为 0 时也返回 None
        assert result["interest_coverage"] is None

    def test_calculate_with_partial_missing_data(self, calculator):
        """测试部分缺失数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"operating_profit": 200000},  # 缺失 interest_expense
            balance_sheet={
                "total_assets": 5000000,
                "total_liabilities": 2000000,
                "current_assets": 1500000,
                "current_liabilities": 800000,
                # 缺失 inventory
                "owner_equity": 3000000,
            },
            cash_flow_sheet={},
        )
        # debt_ratio 和 current_ratio 应该正常计算
        assert result["debt_ratio"] == 0.4000
        assert result["current_ratio"] == 1.8750
        # quick_ratio 缺失 inventory，应返回 None
        assert result["quick_ratio"] is None
        # interest_coverage 缺失 interest_expense，应返回 None
        assert result["interest_coverage"] is None
