"""测试财务分析服务与懒加载的集成"""

from __future__ import annotations
import pytest
from unittest.mock import Mock, patch
from ecox.services.financial_analysis_service import FinancialAnalysisService


def test_financial_analysis_service_has_lazy_loader():
    """测试财务分析服务包含懒加载器"""
    service = FinancialAnalysisService()

    assert hasattr(service, 'lazy_loader')
    assert service.lazy_loader is not None


@patch('ecox.services.lazy_loading_service.LazyLoadingService.get_financial_data')
def test_calculate_metrics_uses_lazy_loader(mock_get_data):
    """测试 calculate_metrics 使用懒加载"""
    # 模拟返回数据
    mock_get_data.return_value = {
        'stock_code': 'SH600000',
        'stock_name': '测试股票',
        'report_date': '2025-12-31',
        'report_type': 'Q4',
        'profit_sheet': {
            'total_revenue': 1000000000,
            'net_profit': 100000000,
        },
        'balance_sheet': {
            'total_assets': 5000000000,
        },
        'cash_flow_sheet': {}
    }

    service = FinancialAnalysisService()
    result = service.calculate_metrics('600000')  # 不带前缀

    # 验证调用了懒加载
    assert mock_get_data.called
    assert mock_get_data.call_args[1]['stock_code'] == '600000'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
