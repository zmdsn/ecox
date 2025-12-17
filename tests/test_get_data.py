import pytest
from ecox.get_data import *

def test_sample():
    secucode = 'SH601390'
    msg = get_dupont_analysis_(secucode)
    print(msg)

def test_code_Format():
    secucode = '  SH601390  '
    msg1 = code_format(secucode)
    secucode2 = 'SH601390'
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