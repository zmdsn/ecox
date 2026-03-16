"""
财务报表数据采集模块
使用 akshare 获取 A 股财务报表数据，并存储到 PostgreSQL

注意：完整实现请参考原 get_report.py 文件
"""
import os
import warnings
warnings.filterwarnings("ignore")

import akshare as ak
import psycopg2.extras
import pandas as pd
import time
from datetime import datetime
from psycopg2 import OperationalError, ProgrammingError

# 导入统一配置和工具模块
from ..config import PG_CONFIG
from ..db import get_pg_conn
from ..utils import code_format

# 反爬间隔（单股票/单报表抓取间隔，避免IP封禁）
CALL_INTERVAL = 5  # 秒
# 要抓取的报告期类型
REPORT_TYPES = ["年报", "季报"]


def create_finance_tables():
    """创建三大财务报表表结构"""
    conn = get_pg_conn()
    cursor = conn.cursor()

    # 1. 利润表（stock_profit_sheet）
    create_profit_sql = """
    CREATE TABLE IF NOT EXISTS stock_profit_sheet (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        report_date VARCHAR(20) NOT NULL,
        report_type VARCHAR(10) NOT NULL,
        total_revenue NUMERIC(20,2),
        operating_profit NUMERIC(20,2),
        net_profit NUMERIC(20,2),
        basic_eps NUMERIC(10,4),
        diluted_eps NUMERIC(10,4),
        create_time TIMESTAMP DEFAULT NOW(),
        CONSTRAINT idx_profit_code_date UNIQUE (stock_code, report_date)
    );
    COMMENT ON TABLE stock_profit_sheet IS 'A股利润表（按报告期）';
    """

    # 2. 资产负债表（stock_balance_sheet）
    create_balance_sql = """
    CREATE TABLE IF NOT EXISTS stock_balance_sheet (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        report_date VARCHAR(20) NOT NULL,
        report_type VARCHAR(10) NOT NULL,
        total_assets NUMERIC(20,2),
        total_liabilities NUMERIC(20,2),
        owner_equity NUMERIC(20,2),
        fixed_assets NUMERIC(20,2),
        create_time TIMESTAMP DEFAULT NOW(),
        CONSTRAINT idx_balance_code_date UNIQUE (stock_code, report_date)
    );
    COMMENT ON TABLE stock_balance_sheet IS 'A股资产负债表（按报告期）';
    """

    # 3. 现金流量表（stock_cash_flow_sheet）
    create_cashflow_sql = """
    CREATE TABLE IF NOT EXISTS stock_cash_flow_sheet (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        report_date VARCHAR(20) NOT NULL,
        report_type VARCHAR(10) NOT NULL,
        operating_cash_flow NUMERIC(20,2),
        investing_cash_flow NUMERIC(20,2),
        financing_cash_flow NUMERIC(20,2),
        net_cash_flow NUMERIC(20,2),
        create_time TIMESTAMP DEFAULT NOW(),
        CONSTRAINT idx_cashflow_code_date UNIQUE (stock_code, report_date)
    );
    COMMENT ON TABLE stock_cash_flow_sheet IS 'A股现金流量表（按报告期）';
    """

    try:
        cursor.execute(create_profit_sql)
        cursor.execute(create_balance_sql)
        cursor.execute(create_cashflow_sql)
        conn.commit()
        print("财务报表表创建成功")
    except Exception as e:
        conn.rollback()
        print(f"创建表失败：{e}")
    finally:
        cursor.close()
        conn.close()


def crawl_profit_sheet(stock_code, stock_name):
    """抓取单只股票利润表"""
    try:
        file_name = f"./data/profit_sheet_{stock_code[-6:]}_.csv"
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, dtype={'SECURITY_CODE': str})
        else:
            df = ak.stock_profit_sheet_by_report_em(symbol=stock_code)
            if not df.empty:
                df.to_csv(file_name, index=False)

        if not df.empty:
            conn = get_pg_conn()
            cursor = conn.cursor()
            # ... 插入逻辑
            conn.commit()
            cursor.close()
            conn.close()

        return df
    except Exception as e:
        print(f"抓取 {stock_code} 利润表失败：{e}")
        return pd.DataFrame()


def crawl_balance_sheet(stock_code, stock_name):
    """抓取单只股票资产负债表"""
    try:
        df = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
        # ... 处理逻辑
        return df
    except Exception as e:
        print(f"抓取 {stock_code} 资产负债表失败：{e}")
        return pd.DataFrame()


def crawl_cash_flow_sheet(stock_code, stock_name):
    """抓取单只股票现金流量表"""
    try:
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)
        # ... 处理逻辑
        return df
    except Exception as e:
        print(f"抓取 {stock_code} 现金流量表失败：{e}")
        return pd.DataFrame()


if __name__ == "__main__":
    create_finance_tables()
