"""集成测试：手动触发实时数据采集"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from datetime import datetime
import pandas as pd
from unittest.mock import patch, MagicMock
from ecox.data.realtime import fetch_job, get_a_share_real_time_data

def create_mock_realtime_data():
    """创建模拟的实时行情数据"""
    data = {
        '代码': ['000001', '000002', '600000', '600519', '000858'],
        '名称': ['平安银行', '万科A', '浦发银行', '贵州茅台', '五粮液'],
        '最新价': [12.50, 8.30, 7.80, 1680.00, 145.20],
        '涨跌额': [0.25, -0.10, 0.05, 15.00, -2.30],
        '涨跌幅': [2.04, -1.19, 0.65, 0.90, -1.56],
        '成交量': [120000000, 95000000, 80000000, 2500000, 35000000],
        '成交额': [1500000000, 788500000, 624000000, 4200000000, 5082000000],
        '最高': [12.65, 8.45, 7.92, 1695.00, 147.50],
        '最低': [12.30, 8.20, 7.75, 1665.00, 144.80],
        '今开': [12.35, 8.35, 7.78, 1670.00, 146.00],
        '昨收': [12.25, 8.40, 7.75, 1665.00, 147.50],
    }
    return pd.DataFrame(data)

def test_manual_fetch_realtime_data():
    """手动触发数据采集，验证数据完整性（使用模拟数据）"""
    print("\n=== 手动触发实时数据采集（模拟模式） ===")

    # 使用模拟数据
    mock_df = create_mock_realtime_data()

    # 模拟 akshare 函数和 insert_stock_data 函数
    with patch('akshare.stock_zh_a_spot', return_value=mock_df):
        with patch('ecox.data.realtime.insert_stock_data') as mock_insert:
            mock_insert.return_value = {'success': 5, 'failed': 0}

            # 执行数据采集
            fetch_job()

            # 验证 insert_stock_data 被调用
            assert mock_insert.called, "insert_stock_data 未被调用"

            # 获取传入 insert_stock_data 的数据
            call_args = mock_insert.call_args[0][0]

            assert not call_args.empty, "数据采集失败，返回空 DataFrame"
            assert len(call_args) >= 5, f"数据量过少，仅 {len(call_args)} 条"
            assert '代码' in call_args.columns, "缺少 '代码' 列"
            assert '最新价' in call_args.columns, "缺少 '最新价' 列"

            # 验证数据有效性
            valid_prices = call_args[call_args['最新价'] > 0]
            assert len(valid_prices) >= 5, f"有效价格数据过少，仅 {len(valid_prices)} 条"

            print(f"✅ 数据采集成功")
            print(f"采集股票数量: {len(call_args)}")
            print(f"有效价格数量: {len(valid_prices)}")
            print(f"前5只股票:")
            print(call_args[['代码', '名称', '最新价', '涨跌幅']].head())

def test_database_save():
    """测试数据保存到数据库（使用模拟数据）"""
    from ecox.services import DataCollectionService

    # 使用模拟数据
    df = create_mock_realtime_data()

    # 取前5条进行测试
    test_df = df.head(5)

    # 转换为字典列表
    data_list = []
    for _, row in test_df.iterrows():
        data = {
            "stock_code": str(row.get("代码")),
            "stock_name": str(row.get("名称")),
            "latest_price": float(row.get("最新价", 0)),
            "price_change": float(row.get("涨跌额", 0)),
            "price_change_rate": float(row.get("涨跌幅", 0)),
            "volume": int(row.get("成交量", 0)),
            "turnover": int(row.get("成交额", 0)),
            "high_price": float(row.get("最高", 0)),
            "low_price": float(row.get("最低", 0)),
            "open_price": float(row.get("今开", 0)),
            "pre_close_price": float(row.get("昨收", 0)),
        }
        data_list.append(data)

    # 保存到数据库
    service = DataCollectionService()
    result = service.save_realtime_data(data_list)

    assert result['success'] > 0, "数据保存失败"
    assert result['failed'] == 0, f"保存失败 {result['failed']} 条"

    print(f"✅ 数据库保存成功")
    print(f"成功: {result['success']} 条")
    print(f"失败: {result['failed']} 条")
