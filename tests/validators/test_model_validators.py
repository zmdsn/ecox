"""测试模型验证器"""

from __future__ import annotations
import pytest
from ecox.validators import (
    ModelValidator,
    ProfitSheetValidator,
    BalanceSheetValidator,
    ValidationSeverity
)


def test_model_validator_missing_required_field():
    """测试缺失必填字段"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        # 缺少 report_date
    }

    issues = validator.validate(data)

    assert len(issues) > 0
    assert any(i.field == 'report_date' for i in issues)


def test_model_validator_negative_revenue():
    """测试负收入"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_revenue': -1000000
    }

    issues = validator.validate(data)

    assert any(i.field == 'total_revenue' and 'cannot be negative' in i.message for i in issues)


def test_model_validator_profit_anomaly():
    """测试利润异常"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_revenue': 1000000,
        'net_profit': 15000000  # 15倍收入
    }

    issues = validator.validate(data)

    assert any(i.field == 'net_profit' and 'anomaly' in i.message for i in issues)


def test_model_validator_sign_inconsistency():
    """测试符号不一致"""
    validator = ModelValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'operating_profit': 1000000,
        'net_profit': -500000
    }

    issues = validator.validate(data)

    assert any('inconsistency' in i.message for i in issues)


def test_profit_sheet_validator_gross_margin():
    """测试毛利率异常"""
    validator = ProfitSheetValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_revenue': 1000000,
        'operating_cost': 3000000  # 导致 -200% 毛利率
    }

    issues = validator.validate(data)

    assert any('margin' in i.message for i in issues)


def test_balance_sheet_validator_debt_ratio():
    """测试资产负债率"""
    validator = BalanceSheetValidator()

    data = {
        'stock_code': 'SH600000',
        'report_date': '2025-12-31',
        'total_assets': 1000000,
        'total_liabilities': 1200000  # > 100%
    }

    issues = validator.validate(data)

    assert any('Debt ratio' in i.message for i in issues)


def test_validation_issue_to_dict():
    """测试 ValidationIssue 转字典"""
    from ecox.validators import ValidationIssue

    issue = ValidationIssue(
        field='test_field',
        message='Test message',
        severity=ValidationSeverity.ERROR,
        value=100
    )

    result = issue.to_dict()
    assert result['field'] == 'test_field'
    assert result['message'] == 'Test message'
    assert result['severity'] == 'error'
    assert result['value'] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
