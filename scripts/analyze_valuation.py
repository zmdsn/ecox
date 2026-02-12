#!/usr/bin/env python
"""
估值分析脚本
根据估值数据进行股票筛选和分析
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecox.db import get_pg_connection
from ecox.valuation.indicators import (
    calculate_valuation_metrics,
    filter_by_valuation,
)


def analyze_undervalued_stocks(min_pe: float = 15.0, max_pb: float = 2.0):
    """分析低估股票"""
    conn = get_pg_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        s.stock_code,
        s.stock_name,
        s.price,
        s.earnings_per_share,
        s.book_value_per_share,
        v.trade_date
    FROM stock_valuation s
    JOIN (
        SELECT stock_code, trade_date, pe, pb
        FROM stock_valuation v
        WHERE v.trade_date = (
            SELECT MAX(trade_date) FROM stock_valuation WHERE stock_code = s.stock_code
        )
    ) latest
    WHERE s.pe > 0 AND s.pb > 0
    ORDER BY s.pe ASC
    LIMIT 50;
    """

    cursor.execute(sql)
    results = cursor.fetchall()

    print("\n=== 低估股票分析 ===")
    print(f"PE < {min_pe}: {len([r for r in results if r[2] < min_pe])}")
    print(f"PB < {max_pb}: {len([r for r in results if r[3] < max_pb])}")

    conn.close()


def industry_comparison():
    """行业估值对比"""
    conn = get_pg_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        s.stock_code,
        s.stock_name,
        s.pe,
        s.pb,
        i.avg_pe,
        i.avg_pb
        s.pe / NULLIF(i.avg_pe, 0) as pe_relative
        s.pb / NULLIF(i.avg_pb, 0) as pb_relative
    FROM stock_valuation s
    JOIN industry_valuation i ON i.industry_code = (
        CASE
            WHEN s.price < s.book_value_per_share THEN '金融'
            WHEN s.price >= s.book_value_per_share * 3 THEN '周期'
            ELSE '其他'
        END
    ) latest
    WHERE s.pe > 0 AND i.avg_pe > 0
    ORDER BY (s.pe / NULLIF(i.avg_pe, 0)) ASC
    LIMIT 20;
    """

    cursor.execute(sql)
    results = cursor.fetchall()

    print("\n=== 行业估值对比 ===")
    for r in results:
        industry = r[8] if r[8] else "未知"
        print(
            f"{r[0]} ({r[1]}) - PE: {r[2]:.2f} (行业{industry}: {r[3] or 'N/A':.2f}, 相对: {r[4] or 'N/A':.2f}x)"
        )

    conn.close()


def valuation_summary():
    """估值汇总统计"""
    conn = get_pg_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        COUNT(DISTINCT stock_code) as total_stocks,
        COUNT(DISTINCT CASE WHEN pe > 0 AND pe < 20 THEN stock_code END) as value_stocks,
        COUNT(DISTINCT CASE WHEN pe > 0 AND pe < 10 THEN stock_code END) as undervalued,
        AVG(pe) as avg_pe,
        AVG(pb) as avg_pb
        AVG(market_cap) as avg_market_cap
    FROM stock_valuation
    WHERE trade_date = (SELECT MAX(trade_date) FROM stock_valuation LIMIT 1)
    """

    cursor.execute(sql)
    result = cursor.fetchone()

    print("\n=== 市场估值汇总 ===")
    print(f"总股票数: {result[0]}")
    print(f"价值股数 (PE<20): {result[1]}")
    print(f"低估股数 (PE<10): {result[2]}")
    print(f"平均 PE: {result[3]:.2f}")
    print(f"平均 PB: {result[4]:.2f}")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="估值分析工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 低估分析
    parser_undervalued = subparsers.add_parser("undervalued", help="分析低估值股票")
    parser_undervalued.add_argument("--min-pe", type=float, default=15.0, help="最大 PE")
    parser_undervalued.add_argument("--max-pb", type=float, default=2.0, help="最大 PB")

    # 行业对比
    subparsers.add_parser("industry", help="行业估值对比")

    # 汇总统计
    subparsers.add_parser("summary", help="估值汇总统计")

    args = parser.parse_args()

    if args.command == "undervalued":
        analyze_undervalued_stocks(args.min_pe, args.max_pb)
    elif args.command == "industry":
        industry_comparison()
    elif args.command == "summary":
        valuation_summary()
    else:
        parser.print_help()
