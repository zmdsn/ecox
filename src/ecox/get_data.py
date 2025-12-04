import akshare as ak
import os
import pandas as pd
import numpy as np
from fastmcp import FastMCP
import uvicorn
from fastmcp.client.transports import StreamableHttpTransport

# 1. 创建 MCP 服务器实例
mcp = FastMCP("财务计算服务器")

def get_data(symbol="SH601390"):
    filename = f"./data/profit_sheet_{symbol}_.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
    else:  
        stock_profit_sheet_by_report_em_df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        stock_balance_sheet_by_report_em_df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        stock_cash_flow_sheet_by_report_em_df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        df = pd.merge(stock_profit_sheet_by_report_em_df, stock_balance_sheet_by_report_em_df, on="REPORT_DATE")
        df = pd.merge(df, stock_cash_flow_sheet_by_report_em_df, on="REPORT_DATE")
        base_list = [x for x in list(df) if not(x.endswith("_x") or x.endswith("_y"))]
        df[base_list].to_csv(filename)
    return df

# get_data(symbol="SH601390")

def generate_dupont_mermaid(df, condition=None):
    if condition:
        df = df[condition]
    return f"""```mermaid
    graph LR
    A[净资产收益率<br>{df['净资产收益率']}]
    A --> B[归属母公司股东的销售净利率<br>{df['归属母公司股东的销售净利率']}]
    A --> C[资产周转率<br>{df['资产周转率']}]
    A --> D[权益乘数<br>{df['权益乘数']}]

    B --> B1[销售净利率<br>{df['销售净利率']}]
    B --> B2[归属母公司股东的净利润占比<br>{df['归属母公司股东的净利润占比']}]
    B1 --> B1a[经营利润率<br>{df['经营利润率']}]
    B1 --> B1b[税负因子<br>{df['税负因子']}]
    B1 --> B1c[利息负担<br>{df['利息负担因子']}]
    B1a --> B1a1[EBIT<br>{df['EBIT']}]
    B1a --> B1a2[营业总收入<br>{df['营业总收入']}]

    B1b --> B1b1[净利润<br>{df['净利润']}]
    B1b --> B1b2[利润总额<br>{df['利润总额']}]

    B1c --> B1c1[利润总额<br>{df['利润总额']}]
    B1c --> B1c2[EBIT<br>{df['EBIT']}]

    B2 --> B2a[归属母公司股东净利润<br>{df['归属母公司股东净利润']}]
    B2 --> B2b[净利润<br>{df['净利润']}]


    C --> C1[营业总收入<br>{df['营业总收入']}]
    C --> C2[平均总资产<br>{df['平均总资产']}]


    D --> D1[平均总资产<br>{df['平均总资产']}]
    D --> D2[平均归属母公司股东权益<br>{df['平均归属母公司股东权益']}]
    D1 --> D1b[期末总资产<br>{df['期末总资产']}]
    D1 --> D1c[期初总资产<br>{df['期初总资产']}]
    D2 --> D2a[期末归属母公司股东权益<br> {df['期末归属母公司股东权益']}]
    D2 --> D2b[期初归属母公司股东权益<br>{df['期初归属母公司股东权益']}]

    ```
    """


def calculate_dupont_analysis(df):
    """
    计算杜邦分析的核心指标并返回结果DataFrame
    参数：
    df: 包含财务数据的DataFrame，需包含以下列：
        - SECURITY_CODE: 证券代码
        - REPORT_DATE: 报告日期
        - TOTAL_ASSETS: 期末总资产
        - TOTAL_PARENT_EQUITY: 期末归属母公司股东权益
        - NETPROFIT_BALANCE: 净利润
        - PARENT_NETPROFIT: 归属母公司股东净利润
        - TOTAL_OPERATE_INCOME: 营业总收入
        - TOTAL_PROFIT: 利润总额
        - INCOME_TAX: 所得税费用
        - INTEREST_EXPENSE: 利息支出
        - OPERATE_PROFIT: 营业利润
    返回：
    结果DataFrame，包含计算出的杜邦分析指标
    """
    # ===================== 1. 数据预处理 =====================
    # 按证券代码、报告日期排序（确保时间顺序）
    df = df.sort_values(by=['SECURITY_CODE', 'REPORT_DATE']).reset_index(drop=True)

    # 补充期初值（按证券分组，取上一期的期末值作为本期期初）
    # 期初总资产
    df['期初总资产'] = df.groupby('SECURITY_CODE')['TOTAL_ASSETS'].shift(1)
    # 期初归属母公司股东权益
    df['期初归属母公司股东权益'] = df.groupby('SECURITY_CODE')['TOTAL_PARENT_EQUITY'].shift(1)
    df['期末总资产'] = df['TOTAL_ASSETS']

    # 处理缺失值（首期数据无期初值，可用本期期末值替代）
    df['期初总资产'] = df['期初总资产'].fillna(df['TOTAL_ASSETS'])
    df['期初归属母公司股东权益'] = df['期初归属母公司股东权益'].fillna(df['TOTAL_PARENT_EQUITY'])

    # ===================== 2. 核心指标计算 =====================
    # 1. 基础利润/收入类
    df['净利润'] = df['NETPROFIT_BALANCE'].fillna(df['TOTAL_PROFIT'] - df['INCOME_TAX'])
    df['归属母公司股东净利润'] = df['PARENT_NETPROFIT']
    df['营业总收入'] = df['TOTAL_OPERATE_INCOME']
    df['利润总额'] = df['TOTAL_PROFIT']
    # （息税前利润）
    df['EBIT'] = df['利润总额'] + df['INTEREST_EXPENSE']

    # 2. 平均资产/权益类
    df['平均总资产'] = (df['TOTAL_ASSETS'] + df['期初总资产']) / 2
    df['平均归属母公司股东权益'] = (df['TOTAL_PARENT_EQUITY'] + df['期初归属母公司股东权益']) / 2
    df['期末归属母公司股东权益'] = df['TOTAL_PARENT_EQUITY']

    # 3. 比率类（杜邦核心）
    # 销售净利率
    df['销售净利率'] = (df['净利润'] / df['营业总收入'] * 100).round(2)
    # 归属母公司股东的销售净利率
    df['归属母公司股东的销售净利率'] = (df['归属母公司股东净利润'] / df['营业总收入'] * 100).round(2)

    # 资产周转率
    df['资产周转率'] = (df['营业总收入'] / df['平均总资产']).round(4)
    # 权益乘数
    df['权益乘数'] = (df['平均总资产'] / df['平均归属母公司股东权益']).round(4)
    # 净资产收益率（ROE）
    df['净资产收益率'] = (df['归属母公司股东净利润'] / df['平均归属母公司股东权益'] * 100).round(2)

    # 4. 辅助分析指标
    # 归属母公司股东的净利润占比
    df['归属母公司股东的净利润占比'] = (df['归属母公司股东净利润'] / df['净利润'] * 100).round(2)
    # 经营利润率
    df['经营利润率'] = (df['OPERATE_PROFIT'] / df['营业总收入'] * 100).round(2)
    # 考虑税负因素
    df['税负因子'] = (df['净利润'] / df['利润总额'] * 100).round(2)
    # 考虑利息负担
    df['利息负担因子'] = (df['EBIT（息税前利润）'] / df['利润总额'] * 100).round(2)

    # ===================== 3. 结果输出 =====================
    # 筛选杜邦分析核心列输出
    # dupont_cols = [
    #     'REPORT_DATE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR',
    #     '营业总收入', '净利润', '归属母公司股东净利润',
    #     '平均总资产', '平均归属母公司股东权益', '归属母公司股东的净利润占比',
    #     '销售净利率', '归属母公司股东的销售净利率', '期末总资产', '期初总资产',
    #     '资产周转率', '权益乘数', '净资产收益率', '期初归属母公司股东权益', '期末归属母公司股东权益',
    #     '经营利润率', '税负因子', '利息负担因子', 'EBIT', '利润总额'
    # ]
    # dupont_result = df[dupont_cols].copy()
    return df


def get_dupont_analysis_(secucode) -> dict:
    df = get_data(secucode)
    return calculate_dupont_analysis(df)

@mcp.tool
def get_dupont_analysis(secucode) -> dict:
    """
    计算净资产收益率 (ROE)。
    Args:
        secucode: 公司代码
    Returns:
        包含ROE计算结果的字典。
    """
    return get_dupont_analysis_(secucode)

# 3. 启动服务器
if __name__ == "__main__":
    # mcp.run()
    # uvicorn.run(mcp, host="0.0.0.0", port=8080)

    # uvicorn.run(
    #         app=mcp,        # FastMCP实例作为app传入
    #         transport="sse",
    #         host="0.0.0.0", # 允许外部访问
    #         port=8080,      # 自定义端口（解决端口指定需求）
    #         reload=True     # 开发模式热重载（可选）
    #     )
    mcp.run(transport="http", host="0.0.0.0", port=8080)