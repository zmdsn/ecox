"""财报下载服务测试"""
from unittest.mock import patch

import pandas as pd

from ecox.services.financial_report_service import FinancialReportService


class TestFinancialReportService:
    """财报下载服务测试"""

    def test_code_format_sh(self):
        """测试上海股票代码格式化"""
        service = FinancialReportService()
        assert service._code_format("600809") == "SH600809"
        assert service._code_format("SH600809") == "SH600809"

    def test_code_format_sz(self):
        """测试深圳股票代码格式化"""
        service = FinancialReportService()
        assert service._code_format("000001") == "SZ000001"
        assert service._code_format("SZ000001") == "SZ000001"

    def test_code_format_other(self):
        """测试其他代码格式化"""
        service = FinancialReportService()
        assert service._code_format("300001") == "SZ300001"
        assert service._code_format("688001") == "SH688001"

    def test_safe_float(self):
        """测试安全浮点转换"""
        assert FinancialReportService._safe_float(123) == 123.0
        assert FinancialReportService._safe_float("123.45") == 123.45
        assert FinancialReportService._safe_float(None) is None
        assert FinancialReportService._safe_float("N/A") is None
        assert FinancialReportService._safe_float("") is None
        assert FinancialReportService._safe_float("-") is None

    @patch('ecox.services.financial_report_service.ak.stock_profit_sheet_by_report_em')
    def test_fetch_profit_sheet_empty(self, mock_ak):
        """测试空数据处理"""
        mock_ak.return_value = pd.DataFrame()
        service = FinancialReportService()
        result = service.fetch_profit_sheet("600809")
        assert result == []

    @patch('ecox.services.financial_report_service.ak.stock_profit_sheet_by_report_em')
    def test_fetch_profit_sheet_success(self, mock_ak):
        """测试成功获取利润表数据"""
        mock_df = pd.DataFrame({
            "股票简称": ["山西汾酒"],
            "报告日期": ["2024-09-30"],
            "报告类型": ["三季报"],
            "营业总收入": [1000000],
            "营业利润": [200000],
            "净利润": [150000],
            "基本每股收益": [1.5]
        })
        mock_ak.return_value = mock_df
        service = FinancialReportService()
        result = service.fetch_profit_sheet("600809")
        assert len(result) == 1
        assert result[0]["stock_code"] == "600809"
        assert result[0]["stock_name"] == "山西汾酒"
        assert result[0]["total_revenue"] == 1000000.0
        assert result[0]["net_profit"] == 150000.0

    @patch('ecox.services.financial_report_service.ak.stock_balance_sheet_by_report_em')
    def test_fetch_balance_sheet_success(self, mock_ak):
        """测试成功获取资产负债表数据"""
        mock_df = pd.DataFrame({
            "股票简称": ["山西汾酒"],
            "报告日期": ["2024-09-30"],
            "报告类型": ["三季报"],
            "资产总计": [5000000],
            "负债合计": [2000000],
            "所有者权益合计": [3000000]
        })
        mock_ak.return_value = mock_df
        service = FinancialReportService()
        result = service.fetch_balance_sheet("600809")
        assert len(result) == 1
        assert result[0]["total_assets"] == 5000000.0
        assert result[0]["owner_equity"] == 3000000.0

    @patch('ecox.services.financial_report_service.ak.stock_cash_flow_sheet_by_report_em')
    def test_fetch_cash_flow_sheet_success(self, mock_ak):
        """测试成功获取现金流量表数据"""
        mock_df = pd.DataFrame({
            "股票简称": ["山西汾酒"],
            "报告日期": ["2024-09-30"],
            "报告类型": ["三季报"],
            "经营活动产生的现金流量净额": [180000],
            "投资活动产生的现金流量净额": [-50000],
            "筹资活动产生的现金流量净额": [-30000]
        })
        mock_ak.return_value = mock_df
        service = FinancialReportService()
        result = service.fetch_cash_flow_sheet("600809")
        assert len(result) == 1
        assert result[0]["operating_cash_flow"] == 180000.0
        assert result[0]["investing_cash_flow"] == -50000.0

    @patch('ecox.services.financial_report_service.ak.stock_profit_sheet_by_report_em')
    def test_fetch_profit_sheet_exception(self, mock_ak):
        """测试异常处理"""
        mock_ak.side_effect = Exception("Network error")
        service = FinancialReportService()
        result = service.fetch_profit_sheet("600809")
        assert result == []
