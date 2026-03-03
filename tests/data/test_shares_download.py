"""
测试股票基础信息下载功能
测试模块: src/ecox/data/shares.py
"""
import pytest
import pandas as pd
from src.ecox.data.shares import get_stock_basic_raw


class TestGetStockBasicRaw:
    """测试 get_stock_basic_raw() 函数"""

    def test_returns_dataframe(self):
        """验证返回类型为 DataFrame"""
        df = get_stock_basic_raw()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """验证必需列存在"""
        df = get_stock_basic_raw()
        required_columns = ["stock_code", "stock_name"]
        for col in required_columns:
            assert col in df.columns, f"缺少列: {col}"

    def test_data_not_empty(self):
        """验证数据非空"""
        df = get_stock_basic_raw()
        assert len(df) > 0, "返回数据为空"

    def test_stock_code_format(self):
        """验证股票代码格式（6位数字）"""
        df = get_stock_basic_raw()
        # 所有代码应该是6位数字
        assert df["stock_code"].str.match(r"^\d{6}$").all(), "股票代码格式错误"

    def test_no_duplicates(self):
        """验证无重复代码"""
        df = get_stock_basic_raw()
        duplicate_count = df["stock_code"].duplicated().sum()
        assert duplicate_count == 0, f"存在 {duplicate_count} 个重复代码"
