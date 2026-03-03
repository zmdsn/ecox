"""财报验证器测试"""
import pytest
from ecox.validators.report_validator import ReportValidator


class TestReportValidator:
    """财报验证器测试"""

    def test_validate_profit_sheet_valid_data(self):
        """测试有效利润表数据"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "stock_name": "测试股票",
            "report_date": "20240930",
            "total_revenue": 1000000000,
            "net_profit": 50000000,
        }
        result = validator.validate_profit_sheet(data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_profit_sheet_negative_revenue(self):
        """测试营业收入为负"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
            "total_revenue": -1000,
        }
        result = validator.validate_profit_sheet(data)
        assert result.is_valid is False
        assert any("negative" in err.lower() or "为负" in err for err in result.errors)

    def test_validate_profit_sheet_missing_core_field(self):
        """测试核心字段缺失（可选字段，所以应该通过）"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
        }
        result = validator.validate_profit_sheet(data)
        # 没有核心字段应该仍然有效（都是可选的）
        assert result.is_valid is True

    def test_validate_balance_sheet_equity_check(self):
        """测试资产负债表勾稽关系"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
            "total_assets": 1000000000,
            "total_liabilities": 300000000,
            "owner_equity": 700000000,
        }
        result = validator.validate_balance_sheet(data)
        assert result.is_valid is True

    def test_validate_balance_sheet_equity_mismatch(self):
        """测试资产负债表勾稽关系不匹配"""
        validator = ReportValidator()
        data = {
            "stock_code": "600809",
            "report_date": "20240930",
            "total_assets": 1000000000,
            "total_liabilities": 300000000,
            "owner_equity": 500000000,  # 不匹配
        }
        result = validator.validate_balance_sheet(data)
        # 勾稽关系不匹配但应该产生警告
        assert result.is_valid is True
        assert len(result.warnings) > 0
