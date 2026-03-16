"""FinancialAnalysisService 统一财务分析服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch

from ecox.services.financial_analysis_service import FinancialAnalysisService
from ecox.calculators import (
    ProfitabilityCalculator,
    CashFlowCalculator,
    SolvencyCalculator,
    EfficiencyCalculator,
    GrowthCalculator,
    ValuationCalculator,
)


class TestFinancialAnalysisService:
    """测试 FinancialAnalysisService 类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return FinancialAnalysisService()

    @pytest.fixture
    def sample_financial_data(self):
        """示例财务数据"""
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
                "current_assets": 1500000,
                "current_liabilities": 800000,
                "inventory": 500000,
            },
            "cash_flow_sheet": {
                "operating_cash_flow": 180000,
                "capex": 50000,
            },
            "stock_name": "测试股票",
            "report_date": "2024-09-30",
            "report_type": "三季报",
        }

    @pytest.fixture
    def sample_market_data(self):
        """示例市场数据"""
        return {
            "market_cap": 6000000,
            "total_debt": 2000000,
            "cash": 500000,
            "ebitda": 300000,
            "earnings_growth": 0.15,
        }

    def test_service_initialization(self, service):
        """测试服务初始化包含所有计算器"""
        assert "profitability" in service.calculators
        assert "cash_flow" in service.calculators
        assert "solvency" in service.calculators
        assert "efficiency" in service.calculators
        assert "growth" in service.calculators
        assert "valuation" in service.calculators

        # 验证计算器类型
        assert isinstance(service.calculators["profitability"], ProfitabilityCalculator)
        assert isinstance(service.calculators["cash_flow"], CashFlowCalculator)
        assert isinstance(service.calculators["solvency"], SolvencyCalculator)
        assert isinstance(service.calculators["efficiency"], EfficiencyCalculator)
        assert isinstance(service.calculators["growth"], GrowthCalculator)
        assert isinstance(service.calculators["valuation"], ValuationCalculator)

    def test_calculate_metrics_with_mock_data(self, service, sample_financial_data):
        """测试使用 mock 数据计算财务指标"""
        result = service.calculate_metrics(
            stock_code="600809",
            report_date="2024-09-30",
            financial_data=sample_financial_data,
        )

        # 验证基本信息
        assert result["stock_code"] == "600809"
        assert result["stock_name"] == "测试股票"
        assert result["report_date"] == "2024-09-30"
        assert result["report_type"] == "三季报"

        # 验证盈利能力指标
        assert "roe" in result
        assert "roa" in result
        assert "gross_margin" in result
        assert "net_margin" in result

        # 验证现金流指标
        assert "fcff" in result
        assert "fcfe" in result
        assert "cash_conversion_rate" in result

        # 验证偿债能力指标
        assert "debt_ratio" in result
        assert "current_ratio" in result
        assert "quick_ratio" in result

    def test_calculate_metrics_with_specific_modules(self, service, sample_financial_data):
        """测试指定模块计算"""
        # 只计算盈利能力和现金流模块
        result = service.calculate_metrics(
            stock_code="600809",
            modules=["profitability", "cash_flow"],
            financial_data=sample_financial_data,
        )

        # 验证盈利能力指标存在
        assert "roe" in result
        assert "roa" in result
        assert "gross_margin" in result
        assert "net_margin" in result

        # 验证现金流指标存在
        assert "fcff" in result
        assert "fcfe" in result

    def test_calculate_metrics_with_valuation(self, service, sample_financial_data, sample_market_data):
        """测试带市场数据的估值计算"""
        result = service.calculate_metrics(
            stock_code="600809",
            financial_data=sample_financial_data,
            market_data=sample_market_data,
        )

        # 验证估值指标
        assert "pe_ratio" in result
        assert "pb_ratio" in result
        assert "ps_ratio" in result

    def test_calculate_metrics_invalid_module(self, service, sample_financial_data):
        """测试无效模块名称"""
        result = service.calculate_metrics(
            stock_code="600809",
            modules=["invalid_module", "profitability"],
            financial_data=sample_financial_data,
        )

        # 无效模块应被忽略，有效模块应正常计算
        assert "roe" in result

    def test_calculate_metrics_empty_data(self, service):
        """测试空财务数据"""
        empty_data = {
            "profit_sheet": {},
            "balance_sheet": {},
            "cash_flow_sheet": {},
            "stock_name": None,
            "report_date": None,
            "report_type": None,
        }

        result = service.calculate_metrics(
            stock_code="600809",
            financial_data=empty_data,
        )

        # 基本信息
        assert result["stock_code"] == "600809"

        # 指标应该都是 None
        assert result.get("roe") is None
        assert result.get("roa") is None

    @patch("ecox.services.financial_analysis_service.get_db_session")
    def test_get_financial_data_from_database(self, mock_db_session, service):
        """测试从数据库获取财务数据"""
        # 模拟数据库会话和查询结果
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db_session.return_value.__exit__ = MagicMock(return_value=False)

        # 模拟利润表记录
        mock_profit = MagicMock()
        mock_profit.stock_code = "600809"
        mock_profit.stock_name = "山西汾酒"
        mock_profit.report_date = "2024-09-30"
        mock_profit.report_type = "三季报"
        mock_profit.net_profit = 150000
        mock_profit.total_revenue = 1000000
        mock_profit.operating_profit = 200000
        mock_profit.basic_eps = 1.5
        mock_profit.extra_data = {"other_field": "value"}

        # 模拟查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_profit
        mock_session.query.return_value = mock_query

        result = service._get_financial_data("600809")

        assert result["stock_name"] == "山西汾酒"
        assert result["report_date"] == "2024-09-30"
        assert result["profit_sheet"]["net_profit"] == 150000
        assert result["profit_sheet"]["other_field"] == "value"

    @patch("ecox.services.financial_analysis_service.get_db_session")
    def test_save_metrics_create_new(self, mock_db_session, service):
        """测试保存新指标记录"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db_session.return_value.__exit__ = MagicMock(return_value=False)

        # 模拟没有现有记录
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query

        metrics = {
            "stock_name": "山西汾酒",
            "report_date": "2024-09-30",
            "report_type": "三季报",
            "roe": 0.05,
            "roa": 0.03,
        }

        result = service.save_metrics("600809", metrics)

        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("ecox.services.financial_analysis_service.get_db_session")
    def test_save_metrics_update_existing(self, mock_db_session, service):
        """测试更新现有指标记录"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db_session.return_value.__exit__ = MagicMock(return_value=False)

        # 模拟现有记录
        mock_existing = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing
        mock_session.query.return_value = mock_query

        metrics = {
            "stock_name": "山西汾酒",
            "report_date": "2024-09-30",
            "report_type": "三季报",
            "roe": 0.06,
            "roa": 0.04,
        }

        result = service.save_metrics("600809", metrics)

        assert result is True
        # 不应该调用 add，因为只是更新
        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()

    @patch("ecox.services.financial_analysis_service.get_db_session")
    def test_save_metrics_exception(self, mock_db_session, service):
        """测试保存异常处理"""
        mock_db_session.side_effect = Exception("Database error")

        metrics = {
            "report_date": "2024-09-30",
        }

        result = service.save_metrics("600809", metrics)

        assert result is False

    def test_calculate_and_save(self, service, sample_financial_data):
        """测试计算并保存方法"""
        with patch("ecox.services.financial_analysis_service.get_db_session") as mock_db:
            # 模拟数据库会话
            mock_session = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()

            result = service.calculate_and_save(
                stock_code="600809",
                financial_data=sample_financial_data,
            )

            assert "metrics" in result
            assert "saved" in result
