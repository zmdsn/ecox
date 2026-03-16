"""EfficiencyCalculator 营运能力计算器单元测试"""

import pytest

from ecox.calculators.efficiency import EfficiencyCalculator


class TestEfficiencyCalculator:
    """测试 EfficiencyCalculator 类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return EfficiencyCalculator()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "profit_sheet": {"total_revenue": 1000000, "operating_cost": 600000},
            "balance_sheet": {
                "total_assets": 5000000,
                "inventory": 300000,
                "accounts_receivable": 200000,
            },
            "cash_flow_sheet": {},
        }

    def test_calculate_inventory_turnover(self, calculator, sample_data):
        """测试存货周转率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # inventory_turnover = 600000 / 300000 = 2.0
        assert result["inventory_turnover"] == 2.0

    def test_calculate_receivables_turnover(self, calculator, sample_data):
        """测试应收账款周转率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # receivables_turnover = 1000000 / 200000 = 5.0
        assert result["receivables_turnover"] == 5.0

    def test_calculate_asset_turnover(self, calculator, sample_data):
        """测试总资产周转率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # asset_turnover = 1000000 / 5000000 = 0.2
        assert result["asset_turnover"] == 0.2

    def test_calculate_with_missing_data(self, calculator):
        """测试缺失数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["inventory_turnover"] is None
        assert result["receivables_turnover"] is None
        assert result["asset_turnover"] is None

    def test_calculate_with_zero_divisor(self, calculator):
        """测试除数为零时返回 None"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000, "operating_cost": 600000},
            balance_sheet={
                "total_assets": 0,
                "inventory": 0,
                "accounts_receivable": 0,
            },
            cash_flow_sheet={},
        )
        # 除数为零时应该返回 None
        assert result["inventory_turnover"] is None
        assert result["receivables_turnover"] is None
        assert result["asset_turnover"] is None

    def test_calculate_with_partial_missing_data(self, calculator):
        """测试部分数据缺失"""
        # 缺少 inventory
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000, "operating_cost": 600000},
            balance_sheet={
                "total_assets": 5000000,
                "accounts_receivable": 200000,
            },
            cash_flow_sheet={},
        )
        assert result["inventory_turnover"] is None
        assert result["receivables_turnover"] == 5.0
        assert result["asset_turnover"] == 0.2

        # 缺少 accounts_receivable
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000, "operating_cost": 600000},
            balance_sheet={
                "total_assets": 5000000,
                "inventory": 300000,
            },
            cash_flow_sheet={},
        )
        assert result["inventory_turnover"] == 2.0
        assert result["receivables_turnover"] is None
        assert result["asset_turnover"] == 0.2

    def test_calculate_with_negative_values(self, calculator):
        """测试负值计算（异常情况）"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000, "operating_cost": 600000},
            balance_sheet={
                "total_assets": -1000000,  # 异常负值
                "inventory": 300000,
                "accounts_receivable": 200000,
            },
            cash_flow_sheet={},
        )
        # 负值应该正常计算（虽然业务上不合理，但技术上允许）
        assert result["asset_turnover"] == -1.0
        assert result["inventory_turnover"] == 2.0
        assert result["receivables_turnover"] == 5.0

    def test_calculate_with_string_values(self, calculator):
        """测试字符串类型的数值"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": "1000000", "operating_cost": "600000"},
            balance_sheet={
                "total_assets": "5000000",
                "inventory": "300000",
                "accounts_receivable": "200000",
            },
            cash_flow_sheet={},
        )
        # 字符串应该被正确转换
        assert result["inventory_turnover"] == 2.0
        assert result["receivables_turnover"] == 5.0
        assert result["asset_turnover"] == 0.2

    def test_calculate_with_none_values(self, calculator):
        """测试 None 值"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": None, "operating_cost": 600000},
            balance_sheet={
                "total_assets": 5000000,
                "inventory": None,
                "accounts_receivable": 200000,
            },
            cash_flow_sheet={},
        )
        # None 值应该导致相应指标返回 None
        assert result["inventory_turnover"] is None
        assert result["receivables_turnover"] is None  # revenue 为 None
        assert result["asset_turnover"] is None  # revenue 为 None
