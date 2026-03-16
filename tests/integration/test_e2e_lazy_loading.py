"""端到端测试：完整的懒加载流程"""

from __future__ import annotations
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

from ecox.services.financial_analysis_service import FinancialAnalysisService


@pytest.mark.integration
def test_stock_code_format_handling():
    """测试各种股票代码格式"""

    test_codes = [
        '601318',      # 无前缀
        'SH601318',    # 已有前缀
        'sh601318',    # 小写前缀
    ]

    service = FinancialAnalysisService()

    # 测试代码格式化功能
    from ecox.utils import code_format

    for code in test_codes:
        formatted = code_format(code)
        assert formatted in ['SH601318', 'SZ601318', 'BJ601318']
        assert len(formatted) == 8  # 2 letter prefix + 6 digits
        print(f"✓ {code} -> {formatted}")


@pytest.mark.integration
def test_financial_service_structure():
    """测试财务分析服务结构"""
    service = FinancialAnalysisService()

    # 验证服务有懒加载器
    assert hasattr(service, 'lazy_loader')
    assert service.lazy_loader is not None

    # 验证服务有计算器
    assert hasattr(service, 'calculators')
    assert 'profitability' in service.calculators
    assert 'cash_flow' in service.calculators
    assert 'solvency' in service.calculators

    print("✓ FinancialAnalysisService structure is correct")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
