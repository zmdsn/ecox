"""
估值数据采集模块
从 akshare 获取估值数据，并存入数据库
"""
import time
import pandas as pd
import akshare as ak
import psycopg2.extras
from typing import Optional, Dict, List

# 导入配置和数据库模块
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root))
from ..config import PG_CONFIG
from ..db import get_pg_conn

# 数据采集间隔
CALL_INTERVAL = 0.5  # 秒


def create_valuation_tables():
    """创建估值数据表"""
    conn = get_pg_conn()
    cursor = conn.cursor()

    # 股票估值表
    create_stock_valuation_sql = """
    CREATE TABLE IF NOT EXISTS stock_valuation (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(100),
        trade_date DATE NOT NULL,
        price NUMERIC(10, 2),
        earnings_per_share NUMERIC(10, 4),
        book_value_per_share NUMERIC(10, 4),
        sales_per_share NUMERIC(10, 4),
        shares_outstanding NUMERIC(18, 2),
        total_revenue NUMERIC(20, 2),
        total_assets NUMERIC(20, 2),
        net_assets NUMERIC(20, 2),
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (stock_code, trade_date)
    );
    COMMENT ON TABLE stock_valuation IS '股票估值数据表';
    CREATE INDEX IF NOT EXISTS idx_valuation_date ON stock_valuation (stock_code, trade_date);
    """

    # 行业估值表
    create_industry_valuation_sql = """
    CREATE TABLE IF NOT EXISTS industry_valuation (
        id SERIAL PRIMARY KEY,
        industry_code VARCHAR(20) PRIMARY KEY,
        industry_name VARCHAR(100),
        trade_date DATE NOT NULL,
        avg_pe NUMERIC(10, 2),
        avg_pb NUMERIC(10, 2),
        avg_ps NUMERIC(10, 2),
        avg_market_cap NUMERIC(20, 2),
        sample_count INTEGER,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (industry_code, trade_date)
    );
    COMMENT ON TABLE industry_valuation IS '行业估值数据表';
    """

    try:
        cursor.execute(create_stock_valuation_sql)
        cursor.execute(create_industry_valuation_sql)
        conn.commit()
        print("估值数据表创建成功")
    except Exception as e:
        conn.rollback()
        print(f"创建表失败：{e}")
    finally:
        cursor.close()
        conn.close()


def fetch_stock_valuation(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    获取单只股票的估值数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：20200101）
        end_date: 截止日期（格式：20231231）

    Returns:
        估值数据 DataFrame
    """
    try:
        df = ak.stock_zh_a_spot_em()

        # 转换数据格式
        if not df.empty:
            df["stock_code"] = stock_code
            df["trade_date"] = pd.to_datetime("today").date()

        return df

    except Exception as e:
        print(f"获取 {stock_code} 估值数据失败：{e}")
        return pd.DataFrame()


def fetch_industry_valuation(
    industry: str,
    trade_date: Optional[str] = None
) -> Dict:
    """
    获取行业平均估值指标

    Args:
        industry: 行业代码或名称
        trade_date: 交易日期

    Returns:
        行业估值指标字典
    """
    try:
        # 这里可以从 stock_valuation 表计算行业平均
        # 或者从 akshare 获取行业分类数据

        return {
            "avg_pe": 15.0,  # 示例数据
            "avg_pb": 2.5,
            "avg_ps": 5.0,
            "avg_market_cap": 1000000000,
        }

    except Exception as e:
        print(f"获取 {industry} 行业估值失败：{e}")
        return {}


def save_valuation_to_db(
    df: pd.DataFrame,
    table_name: str = "stock_valuation"
) -> int:
    """
    将估值数据保存到数据库

    Args:
        df: 估值数据
        table_name: 表名

    Returns:
        插入的记录数
    """
    if df.empty:
        print("无数据可保存")
        return 0

    conn = get_pg_conn()
    cursor = conn.cursor()

    insert_sql = f"""
    INSERT INTO {table_name} (
        stock_code, stock_name, trade_date,
        price, earnings_per_share, book_value_per_share, sales_per_share,
        shares_outstanding, total_revenue, total_assets, net_assets
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
        price = EXCLUDED.price,
        earnings_per_share = EXCLUDED.earnings_per_share,
        book_value_per_share = EXCLUDED.book_value_per_share,
        sales_per_share = EXCLUDED.sales_per_share,
        shares_outstanding = EXCLUDED.shares_outstanding,
        total_revenue = EXCLUDED.total_revenue,
        total_assets = EXCLUDED.total_assets,
        net_assets = EXCLUDED.net_assets,
        update_time = CURRENT_TIMESTAMP
    """

    data_tuples = [
        (
            row["stock_code"],
            row.get("stock_name", ""),
            row["trade_date"],
            float(row.get("price", 0)),
            float(row.get("earnings_per_share", 0)),
            float(row.get("book_value_per_share", 0)),
            float(row.get("sales_per_share", 0)),
            float(row.get("shares_outstanding", 0)),
            float(row.get("total_revenue", 0)),
            float(row.get("total_assets", 0)),
            float(row.get("net_assets", 0)),
        )
        for _, row in df.iterrows()
    ]

    try:
        psycopg2.extras.execute_batch(cursor, insert_sql, data_tuples, page_size=100)
        conn.commit()
        inserted = cursor.rowcount
        print(f"成功保存 {inserted} 条估值数据")
        return inserted

    except Exception as e:
        conn.rollback()
        print(f"保存估值数据失败：{e}")
        return 0

    finally:
        cursor.close()
        conn.close()


def fetch_valuation_data(
    stock_codes: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    批量获取估值数据

    Args:
        stock_codes: 股票代码列表，None 表示全市场
        start_date: 开始日期
        end_date: 截止日期

    Returns:
        合并的估值数据 DataFrame
    """
    all_data = []

    if stock_codes is None:
        # 获取全市场股票列表
        from akshare as ak
        stock_info = ak.stock_info_a_code_name()
        stock_codes = stock_info["code"].tolist()[:50]  # 限制数量

    for code in stock_codes:
        df = fetch_stock_valuation(code, start_date, end_date)
        if not df.empty:
            all_data.append(df)
        time.sleep(CALL_INTERVAL)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


def update_industry_valuation(trade_date: Optional[str] = None):
    """
    更新行业估值指标
    从 stock_valuation 表计算各行业的平均估值指标

    Args:
        trade_date: 交易日期

    Returns:
        更新的行业数量
    """
    conn = get_pg_conn()
    cursor = conn.cursor()

    try:
        # 按行业分组计算平均指标
        update_sql = """
        WITH industry_metrics AS (
            SELECT
                i.industry_code,
                AVG(v.pe) as avg_pe,
                AVG(v.pb) as avg_pb,
                AVG(v.ps) as avg_ps,
                AVG(v.market_cap) as avg_market_cap,
                COUNT(*) as sample_count
            FROM stock_valuation v
            WHERE v.trade_date = %s
            GROUP BY i.industry_code
        )
        UPDATE industry_valuation iv
        SET
            avg_pe = im.avg_pe,
            avg_pb = im.avg_pb,
            avg_ps = im.avg_ps,
            avg_market_cap = im.avg_market_cap,
            sample_count = im.sample_count,
            update_time = CURRENT_TIMESTAMP
        FROM industry_metrics im
        WHERE iv.trade_date = %s OR iv.trade_date IS NULL
        """

        cursor.execute(update_sql, (trade_date,))
        conn.commit()

        updated = cursor.rowcount
        print(f"更新了 {updated} 个行业的估值指标")
        return updated

    except Exception as e:
        conn.rollback()
        print(f"更新行业估值失败：{e}")
        return 0

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # 测试数据采集
    create_valuation_tables()

    # 获取测试数据
    test_df = fetch_stock_valuation("600000")

    if not test_df.empty:
        print("测试数据：")
        print(test_df[["stock_code", "price", "pe"]].head())

        # 保存到数据库
        save_valuation_to_db(test_df)
