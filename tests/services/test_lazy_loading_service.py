"""测试懒加载服务"""

from __future__ import annotations
import pytest
import threading
from datetime import datetime
from ecox.services.lazy_loading_service import LazyLoadingService
from ecox.exceptions import ExternalDataSourceError


def test_lazy_loading_service_init():
    """测试服务初始化"""
    service = LazyLoadingService()

    assert service._memory_cache == {}
    assert isinstance(service._downloading, type(threading.Lock()))
    assert service._download_queue == set()


def test_get_cache_key():
    """测试缓存键生成"""
    service = LazyLoadingService()

    key1 = service._get_cache_key('SH600000', None)
    key2 = service._get_cache_key('SH600000', '2025-12-31')

    assert key1 == 'SH600000_latest'
    assert key2 == 'SH600000_2025-12-31'


def test_infer_report_type():
    """测试报告类型推断"""
    service = LazyLoadingService()

    assert service._infer_report_type('2025-03-31') == 'Q1'
    assert service._infer_report_type('2025-06-30') == 'Q2'
    assert service._infer_report_type('2025-09-30') == 'Q3'
    assert service._infer_report_type('2025-12-31') == 'Q4'
    assert service._infer_report_type('2025-05-15') == 'Unknown'


def test_memory_cache_operations():
    """测试内存缓存操作"""
    service = LazyLoadingService()

    # 初始状态
    assert service._check_memory_cache('SH600000', None) is None

    # 更新缓存
    test_data = {'stock_code': 'SH600000', 'test': 'data'}
    service._update_memory_cache('SH600000', None, test_data)

    # 检查缓存
    cached = service._check_memory_cache('SH600000', None)
    assert cached == test_data


def test_invalidate_cache():
    """测试缓存失效"""
    service = LazyLoadingService()

    # 添加缓存
    service._update_memory_cache('SH600000', None, {'test': 'data1'})
    service._update_memory_cache('SZ000001', None, {'test': 'data2'})

    # 清除特定股票缓存
    service.invalidate_cache('SH600000')

    assert service._check_memory_cache('SH600000', None) is None
    assert service._check_memory_cache('SZ000001', None) is not None


def test_invalidate_all_cache():
    """测试清除所有缓存"""
    service = LazyLoadingService()

    service._update_memory_cache('SH600000', None, {'test': 'data'})

    service.invalidate_cache()

    assert service._check_memory_cache('SH600000', None) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
