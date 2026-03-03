#!/usr/bin/env python3
"""财务报表下载脚本"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from ecox.services.financial_report_service import FinancialReportService
import argparse


def main():
    parser = argparse.ArgumentParser(description="财务报表下载工具")
    parser.add_argument("--stock", help="股票代码")
    parser.add_argument("--batch", action="store_true", help="批量下载")
    parser.add_argument("--limit", type=int, help="最多下载数量")
    args = parser.parse_args()
    service = FinancialReportService()

    if args.stock:
        result = service.fetch_all_reports(args.stock)
        print(f"下载完成: 利润表 {len(result['profit'])} 条, 资产负债表 {len(result['balance'])} 条, 现金流量表 {len(result['cash_flow'])} 条")
    elif args.batch:
        result = service.batch_fetch_all_stocks(limit=args.limit)
        print(f"批量下载完成: {result}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
