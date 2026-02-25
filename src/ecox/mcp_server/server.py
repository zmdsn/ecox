"""
MCP 服务器模块
提供 HTTP API 服务，包括杜邦分析和 SQL 查询工具
"""

# 标准库
import os
import sys
from pathlib import Path

# 第三方库
import akshare as ak
import pandas as pd
import psycopg2.extras
from fastmcp import FastMCP
from psycopg2 import DatabaseError, OperationalError, ProgrammingError

# 本地模块
_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root))
from ecox.db import get_pg_conn
from ecox.utils import code_format

# 创建 MCP 服务器实例
mcp = FastMCP("财务计算服务器")


def get_data(symbol="SH601390"):
    """获取股票财务数据"""
    filename = f"./data/profit_sheet_{symbol}_.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
    else:
        stock_profit_sheet_by_report_em_df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        stock_balance_sheet_by_report_em_df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        stock_cash_flow_sheet_by_report_em_df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        df = pd.merge(
            stock_profit_sheet_by_report_em_df,
            stock_balance_sheet_by_report_em_df,
            on="REPORT_DATE",
        )
        df = pd.merge(df, stock_cash_flow_sheet_by_report_em_df, on="REPORT_DATE")
        base_list = [x for x in list(df) if not (x.endswith("_x") or x.endswith("_y"))]
        df[base_list].to_csv(filename)
    return df


def generate_dupont_mermaid(df, condition=None):
    """生成杜邦分析 Mermaid 图表"""
    if condition:
        df = df[condition]
    return f"""```mermaid
    graph LR
    A[净资产收益率<br>{df['净资产收益率']}]
    A --> B[归属母公司股东的销售净利率<br>{df['归属母公司股东的销售净利率']}]
    A --> C[资产周转率<br>{df['资产周转率']}]
    A --> D[权益乘数<br>{df['权益乘数']}]
    ...
```"""


def calculate_dupont_analysis(df):
    """计算杜邦分析的核心指标并返回结果DataFrame"""
    df = df.sort_values(by=["SECURITY_CODE", "REPORT_DATE"]).reset_index(drop=True)

    df["期初总资产"] = df.groupby("SECURITY_CODE")["TOTAL_ASSETS"].shift(1)
    df["期初归属母公司股东权益"] = df.groupby("SECURITY_CODE")["TOTAL_PARENT_EQUITY"].shift(1)
    df["期末总资产"] = df["TOTAL_ASSETS"]

    df["期初总资产"] = df["期初总资产"].fillna(df["TOTAL_ASSETS"])
    df["期初归属母公司股东权益"] = df["期初归属母公司股东权益"].fillna(df["TOTAL_PARENT_EQUITY"])

    df["净利润"] = df["NETPROFIT_BALANCE"].fillna(df["TOTAL_PROFIT"] - df["INCOME_TAX"])
    df["归属母公司股东净利润"] = df["PARENT_NETPROFIT"]
    df["营业总收入"] = df["TOTAL_OPERATE_INCOME"]
    df["利润总额"] = df["TOTAL_PROFIT"]
    df["EBIT"] = df["利润总额"] + df["INTEREST_EXPENSE"]

    df["平均总资产"] = (df["TOTAL_ASSETS"] + df["期初总资产"]) / 2
    df["平均归属母公司股东权益"] = (df["TOTAL_PARENT_EQUITY"] + df["期初归属母公司股东权益"]) / 2
    df["期末归属母公司股东权益"] = df["TOTAL_PARENT_EQUITY"]

    df["销售净利率"] = (df["净利润"] / df["营业总收入"] * 100).round(2)
    df["归属母公司股东的销售净利率"] = (df["归属母公司股东净利润"] / df["营业总收入"] * 100).round(
        2
    )
    df["资产周转率"] = (df["营业总收入"] / df["平均总资产"]).round(4)
    df["权益乘数"] = (df["平均总资产"] / df["平均归属母公司股东权益"]).round(4)
    df["净资产收益率"] = (df["归属母公司股东净利润"] / df["平均归属母公司股东权益"] * 100).round(2)

    df["归属母公司股东的净利润占比"] = (df["归属母公司股东净利润"] / df["净利润"] * 100).round(2)
    df["经营利润率"] = (df["OPERATE_PROFIT"] / df["营业总收入"] * 100).round(2)
    df["税负因子"] = (df["净利润"] / df["利润总额"] * 100).round(2)
    df["利息负担因子"] = (df["EBIT"] / df["利润总额"] * 100).round(2)

    return df


def dupont_analysis_json(df) -> dict:
    """将杜邦分析结果转换为 JSON"""
    dupont_cols = [
        "REPORT_DATE",
        "SECURITY_CODE",
        "SECURITY_NAME_ABBR",
        "营业总收入",
        "净利润",
        "归属母公司股东净利润",
        "平均总资产",
        "平均归属母公司股东权益",
        "归属母公司股东的净利润占比",
        "销售净利率",
        "归属母公司股东的销售净利率",
        "期末总资产",
        "期初总资产",
        "资产周转率",
        "权益乘数",
        "净资产收益率",
        "期初归属母公司股东权益",
        "期末归属母公司股东权益",
        "经营利润率",
        "税负因子",
        "利息负担因子",
        "EBIT",
        "利润总额",
    ]
    dupont_result = calculate_dupont_analysis(df)
    dupont_result = dupont_result[dupont_cols].copy()
    return dupont_result.to_json(orient="records", force_ascii=False)


def get_dupont_analysis_(secucode) -> dict:
    """获取杜邦分析结果"""
    df = get_data(secucode)
    df_dupont = calculate_dupont_analysis(df)
    return generate_dupont_mermaid(df_dupont.iloc[0])


def run_sql(sql):
    """执行 SQL 并返回结果"""
    conn = None
    cursor = None
    result = {"data": None}

    try:
        conn = get_pg_conn()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(sql)
        conn.commit()

        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result["data"] = [dict(row) for row in rows]
        else:
            result["data"] = cursor.rowcount

    except ProgrammingError as e:
        if conn:
            conn.rollback()
        result["error"] = f"SQL 语法/逻辑错误：{str(e)}"
        print(result["error"])
    except OperationalError as e:
        if conn:
            conn.rollback()
        result["error"] = f"数据库连接/操作错误：{str(e)}"
        print(result["error"])
    except DatabaseError as e:
        if conn:
            conn.rollback()
        result["error"] = f"数据库执行错误：{str(e)}"
        print(result["error"])
    except Exception as e:
        if conn:
            conn.rollback()
        result["error"] = f"未知错误：{str(e)}"
        print(result["error"])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return result


# MCP 工具函数
@mcp.tool
async def get_dupont_analysis(secucode: str) -> str:
    """杜邦分析计算工具"""
    return get_dupont_analysis_(code_format(secucode))


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool
def get_sql_data(sql: str = "") -> dict:
    """执行 SQL 查询"""
    return run_sql(sql)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8080)
