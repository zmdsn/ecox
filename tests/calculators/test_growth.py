"""GrowthCalculator 成长能力计算器单元测试"""

import pytest

from ecox.calculators.growth import GrowthCalculator


class TestGrowthCalculator:
    """测试 GrowthCalculator 类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return GrowthCalculator()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "profit_sheet": {
                "total_revenue": 1000000,
                "prev_total_revenue": 850000,
                "net_profit": 150000,
                "prev_net_profit": 120000,
                "revenue_history": [500000, 600000, 720000, 850000, 1000000],
                "profit_history": [80000, 90000, 105000, 120000, 150000],
                "fcff_history": [60000, 70000, 80000, 90000, 100000],
            },
            "balance_sheet": {},
            "cash_flow_sheet": {},
        }

    def test_calculate_revenue_growth_1y(self, calculator, sample_data):
        """测试收入增长率(1年)计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # revenue_growth_1y = (1000000 - 850000) / 850000 = 0.1764705...
        assert result["revenue_growth_1y"] == 0.1765

    def test_calculate_profit_growth_1y(self, calculator, sample_data):
        """测试利润增长率(1年)计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # profit_growth_1y = (150000 - 120000) / 120000 = 0.25
        assert result["profit_growth_1y"] == 0.2500

    def test_calculate_revenue_cagr_5y(self, calculator, sample_data):
        """测试收入5年复合增长率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # revenue_cagr_5y = (1000000 / 500000) ^ (1/4) - 1
        # = 2 ^ 0.25 - 1 = 0.1892071...
        assert result["revenue_cagr_5y"] == 0.1892

    def test_calculate_profit_cagr_5y(self, calculator, sample_data):
        """测试利润5年复合增长率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # profit_cagr_5y = (150000 / 80000) ^ (1/4) - 1
        # = 1.875 ^ 0.25 - 1 = 0.1702...
        assert result["profit_cagr_5y"] == 0.1702

    def test_calculate_fcff_cagr_5y(self, calculator, sample_data):
        """测试 FCF 5年复合增长率计算"""
        result = calculator.calculate(
            profit_sheet=sample_data["profit_sheet"],
            balance_sheet=sample_data["balance_sheet"],
            cash_flow_sheet=sample_data["cash_flow_sheet"],
        )
        # fcff_cagr_5y = (100000 / 60000) ^ (1/4) - 1
        # = 1.6666... ^ 0.25 - 1 = 0.1362...
        assert result["fcff_cagr_5y"] == 0.1362

    def test_calculate_with_missing_revenue_data(self, calculator):
        """测试缺失营收数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"net_profit": 150000, "prev_net_profit": 120000},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["revenue_growth_1y"] is None
        assert result["revenue_cagr_5y"] is None

    def test_calculate_with_missing_profit_data(self, calculator):
        """测试缺失利润数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={"total_revenue": 1000000, "prev_total_revenue": 850000},
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["profit_growth_1y"] is None
        assert result["profit_cagr_5y"] is None

    def test_calculate_with_missing_fcff_history(self, calculator):
        """测试缺失 FCF 历史数据时返回 None"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 1000000,
                "prev_total_revenue": 850000,
                "net_profit": 150000,
                "prev_net_profit": 120000,
                "revenue_history": [500000, 600000, 720000, 850000, 1000000],
                "profit_history": [80000, 90000, 105000, 120000, 150000],
            },
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["fcff_cagr_5y"] is None

    def test_calculate_with_insufficient_history_data(self, calculator):
        """测试历史数据不足5个数据点时返回 None"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 1000000,
                "prev_total_revenue": 850000,
                "net_profit": 150000,
                "prev_net_profit": 120000,
                "revenue_history": [850000, 1000000],  # 只有2个数据点
                "profit_history": [120000, 150000],  # 只有2个数据点
                "fcff_history": [90000, 100000],  # 只有2个数据点
            },
            balance_sheet={},
            cash_flow_sheet={},
        )
        # 1年增长率应该正常计算
        assert result["revenue_growth_1y"] == 0.1765
        assert result["profit_growth_1y"] == 0.2500
        # 5年CAGR需要至少5个数据点
        assert result["revenue_cagr_5y"] is None
        assert result["profit_cagr_5y"] is None
        assert result["fcff_cagr_5y"] is None

    def test_calculate_with_zero_prev_revenue(self, calculator):
        """测试上期营收为零时返回 None"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 1000000,
                "prev_total_revenue": 0,
                "net_profit": 150000,
                "prev_net_profit": 120000,
            },
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["revenue_growth_1y"] is None

    def test_calculate_with_zero_prev_profit(self, calculator):
        """测试上期利润为零时返回 None"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 1000000,
                "prev_total_revenue": 850000,
                "net_profit": 150000,
                "prev_net_profit": 0,
            },
            balance_sheet={},
            cash_flow_sheet={},
        )
        assert result["profit_growth_1y"] is None

    def test_calculate_with_zero_start_value_in_cagr(self, calculator):
        """测试CAGR起始值为零或负数时返回 None"""
        result = calculator.calculate(
            profit_sheet={
                "revenue_history": [0, 600000, 720000, 850000, 1000000],
                "profit_history": [80000, 90000, 105000, 120000, 150000],
            },
            balance_sheet={},
            cash_flow_sheet={},
        )
        # 起始值为0，无法计算CAGR
        assert result["revenue_cagr_5y"] is None
        # profit_cagr_5y 应该正常计算
        assert result["profit_cagr_5y"] == 0.1702

    def test_calculate_with_negative_growth(self, calculator):
        """测试负增长情况"""
        result = calculator.calculate(
            profit_sheet={
                "total_revenue": 800000,
                "prev_total_revenue": 1000000,
                "net_profit": 100000,
                "prev_net_profit": 150000,
                "revenue_history": [1000000, 950000, 900000, 850000, 800000],
                "profit_history": [150000, 140000, 130000, 120000, 100000],
                "fcff_history": [80000, 75000, 70000, 65000, 60000],
            },
            balance_sheet={},
            cash_flow_sheet={},
        )
        # 收入增长率 = (800000 - 1000000) / 1000000 = -0.2
        assert result["revenue_growth_1y"] == -0.2000
        # 利润增长率 = (100000 - 150000) / 150000 = -0.3333...
        assert result["profit_growth_1y"] == -0.3333
        # revenue_cagr_5y = (800000 / 1000000) ^ 0.25 - 1 = -0.0542...
        assert result["revenue_cagr_5y"] == -0.0543

    def test_calculate_cagr_static_method(self, calculator):
        """测试 _calculate_cagr 静态方法"""
        # 测试正常情况
        cagr = GrowthCalculator._calculate_cagr(1000000, 500000, 4)
        assert cagr == 0.1892

        # 测试起始值为零
        cagr = GrowthCalculator._calculate_cagr(1000000, 0, 4)
        assert cagr is None

        # 测试起始值为负数
        cagr = GrowthCalculator._calculate_cagr(1000000, -100, 4)
        assert cagr is None

        # 测试年数为零
        cagr = GrowthCalculator._calculate_cagr(1000000, 500000, 0)
        assert cagr is None

        # 测试结束值为负数（允许负增长）
        cagr = GrowthCalculator._calculate_cagr(500000, 1000000, 4)
        assert cagr == -0.1591
