"""
数据采集模块测试
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecox.get_data import code_format, get_dupont_analysis_


def test_sample():
    """测试杜邦分析"""
    secucode = "SH601390"
    msg = get_dupont_analysis_(secucode)
    print(msg)


def test_code_format():
    """测试股票代码格式化"""
    secucode = "  SH601390  "
    msg1 = code_format(secucode)
    secucode2 = "SH601390"
    msg2 = code_format(secucode2)
    assert msg1 == msg2


def test_code_format_various():
    """测试各种股票代码格式"""
    from ecox.utils import code_format, is_sh_stock, is_sz_stock, parse_stock_code

    # 沪市
    assert code_format("600000") == "SH600000"
    assert is_sh_stock("600000")
    assert not is_sz_stock("600000")

    # 深市
    assert code_format("000001") == "SZ000001"
    assert is_sz_stock("000001")
    assert not is_sh_stock("000001")

    # 带前缀
    assert code_format("SH600000") == "SH600000"
    assert code_format("SZ000001") == "SZ000001"

    # 解析测试
    exchange, code = parse_stock_code("SH600000")
    assert exchange == "SH"
    assert code == "600000"

    print("所有工具函数测试通过")
