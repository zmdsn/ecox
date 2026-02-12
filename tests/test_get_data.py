"""
数据采集模块测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecox.get_data import get_dupont_analysis_, code_format


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


# import asyncio
# from fastmcp import Client

# async def main():
#     async with Client("https://gofastmcp.com/mcp") as client:
#         result = await client.call_tool(
#             name="SearchFastMcp",
#             arguments={"query": "部署 FastMCP 服务器"}
#         )
#     print(result)

# asyncio.run(main())
