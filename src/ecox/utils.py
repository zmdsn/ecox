"""
工具函数模块
提供股票代码格式化等通用工具函数
"""


def code_format(secucode: str) -> str:
    """
    格式化股票代码为标准格式（交易所前缀 + 代码）

    规则：
    - 深市主板：代码以0开头 -> SZ + 代码
    - 深市创业板：代码以3开头 -> SZ + 代码
    - 深市B股：代码以2开头 -> SZ + 代码
    - 沪市主板：代码以6开头 -> SH + 代码
    - 沪市科创板：代码以688开头 -> SH + 代码
    - 北交所：代码以4或8开头 -> BJ + 代码

    Args:
        secucode: 股票代码（可带或不带交易所前缀）

    Returns:
        str: 标准格式的股票代码（如 SH600000、SZ000001）

    Examples:
        >>> code_format("600000")
        'SH600000'
        >>> code_format("000001")
        'SZ000001'
        >>> code_format("sh600000")
        'SH600000'
        >>> code_format("SH600000")
        'SH600000'
    """
    # 类型转换
    if not isinstance(secucode, str):
        secucode = str(secucode)

    secucode = secucode.strip()

    # 空值处理
    if not secucode:
        return secucode

    first = secucode[0].upper()

    # 如果已经带有交易所前缀，直接返回大写格式
    if first in ("S", "B") and len(secucode) > 1:
        return secucode.upper()

    # 深市：0（主板）、2（B股）、3（创业板）
    if first in ("0", "2", "3"):
        return "SZ" + secucode

    # 北交所：4、8、920
    if first == "9" and secucode.startswith("920"):
        return "BJ" + secucode
    if first in ("4", "8"):
        return "BJ" + secucode

    # 沪市：6（主板/科创板）、9（B股）
    if first in ("6", "9"):
        return "SH" + secucode

    # 默认尝试北交所前缀
    return "BJ" + secucode


def parse_stock_code(full_code: str) -> tuple[str, str]:
    """
    解析完整股票代码，返回（交易所，代码）元组

    Args:
        full_code: 完整股票代码（如 SH600000）

    Returns:
        tuple: (交易所, 股票代码) 如 ("SH", "600000")

    Examples:
        >>> parse_stock_code("SH600000")
        ('SH', '600000')
        >>> parse_stock_code("600000")
        ('', '600000')
    """
    if not isinstance(full_code, str):
        full_code = str(full_code)

    full_code = full_code.strip().upper()

    if len(full_code) >= 8 and full_code[:2] in ("SH", "SZ", "BJ"):
        return full_code[:2], full_code[2:]

    return "", full_code


def is_sh_stock(code: str) -> bool:
    """判断是否为沪市股票"""
    _, stock_code = parse_stock_code(code)
    first = stock_code[0] if stock_code else ""
    return first in ("6", "9")


def is_sz_stock(code: str) -> bool:
    """判断是否为深市股票"""
    _, stock_code = parse_stock_code(code)
    first = stock_code[0] if stock_code else ""
    return first in ("0", "2", "3")


def is_bj_stock(code: str) -> bool:
    """判断是否为北交所股票"""
    _, stock_code = parse_stock_code(code)
    first = stock_code[0] if stock_code else ""
    return first in ("4", "8") or (first == "9" and stock_code.startswith("92"))
