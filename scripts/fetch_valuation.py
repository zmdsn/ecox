#!/usr/bin/env python
"""
估值数据采集脚本

使用方法：
1. 采集估值数据（全市场或指定股票）
   uv run python scripts/fetch_valuation.py

2. 更新行业估值指标
   uv run python scripts/fetch_valuation.py --update-industry

3. 分析估值数据
   uv run python scripts/analyze_valuation.py
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecox.valuation.fetcher import (
    create_valuation_tables,
    fetch_valuation_data,
    save_valuation_to_db,
    update_industry_valuation,
)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="估值数据采集工具")
    parser.add_argument(
        "--update-industry",
        action="store_true",
        help="更新行业估值指标",
    )
    parser.add_argument(
        "--stock-codes",
        type=str,
        help="股票代码，逗号分隔（如：600000,000001）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="单次采集股票数量限制",
    )

    args = parser.parse_args()

    # 初始化数据库表
    create_valuation_tables()

    if args.update_industry:
        # 更新行业估值指标
        print("开始更新行业估值指标...")
        updated = update_industry_valuation()
        print(f"完成！更新了 {updated} 个行业")
    else:
        # 采集估值数据
        stock_codes = args.stock_codes.split(",") if args.stock_codes else None

        print(f"开始采集估值数据...")
        print(f"股票数量: {len(stock_codes) if stock_codes else '全市场'}")
        print(f"数量限制: {args.limit}")

        df = fetch_valuation_data(
            stock_codes=stock_codes,
            limit=args.limit,
        )

        if not df.empty:
            # 保存到数据库
            saved = save_valuation_to_db(df, table_name="stock_valuation")
            print(f"完成！保存了 {saved} 条估值数据")
        else:
            print("未获取到估值数据")


if __name__ == "__main__":
    main()
