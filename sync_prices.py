"""
从现有的 stock_daily_data 表同步数据到新的 stock_price 表
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import argparse
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import func

from ecox.database import get_db_session
from ecox import models

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def sync_stock_to_price_table(stock_code: str, days: int = 365) -> dict:
    """从 stock_daily_data 表同步数据到 stock_price 表"""
    logger.info(f"开始同步 {stock_code} 的数据（最近 {days} 天）")

    with get_db_session() as session:
        # 获取日线数据
        daily_data = session.query(
            models.StockDailyData
        ).filter(
            models.StockDailyData.stock_code == stock_code
        ).order_by(
            models.StockDailyData.trade_date.desc()
        ).limit(days).all()

        if not daily_data:
            logger.warning(f"stock_daily_data 中没有 {stock_code} 的数据")
            return {"synced": 0, "skipped": 0}

        logger.info(f"找到 {len(daily_data)} 条日线数据")

        synced = 0
        skipped = 0

        for d in daily_data:
            # 检查是否已存在
            existing = session.query(models.StockPrice).filter(
                models.StockPrice.stock_code == stock_code,
                models.StockPrice.trade_date == d.trade_date,
            ).first()

            if existing:
                skipped += 1
            else:
                # 计算涨跌幅
                prev_close = session.query(
                    models.StockDailyData.close
                ).filter(
                    models.StockDailyData.stock_code == stock_code,
                    models.StockDailyData.trade_date < d.trade_date,
                ).order_by(
                    models.StockDailyData.trade_date.desc()
                ).first()

                change_rate = None
                if prev_close:
                    prev = float(prev_close.close)
                    curr = float(d.close) if d.close else 0
                    change_rate = ((curr - prev) / prev) * 100 if prev > 0 else 0

                price = models.StockPrice(
                    stock_code=stock_code,
                    trade_date=d.trade_date,
                    close_price=float(d.close) if d.close else None,
                    open_price=float(d.open) if d.open else None,
                    high_price=float(d.high) if d.high else None,
                    low_price=float(d.low) if d.low else None,
                    volume=int(d.volume) if d.volume else None,
                    amount=float(d.amount) if d.amount else None,
                    change_rate=change_rate,
                )
                session.add(price)
                synced += 1

        session.commit()
        logger.info(f"同步完成: 新增 {synced} 条, 跳过 {skipped} 条")

        return {"synced": synced, "skipped": skipped, "total": len(daily_data)}


def query_price_table(stock_code: str, days: int = 30) -> None:
    """查询 stock_price 表中的数据"""
    from ecox.services.price_service import PriceService

    price_service = PriceService()
    prices = price_service.get_latest_price(stock_code, days)

    if prices:
        print(f"\n{'='*70}")
        print(f"股票: {stock_code}")
        print(f"最近 {len(prices)} 天价格数据")
        print(f"{'='*70}")

        print(f"{'日期':<12} {'收盘':<10} {'开盘':<10} {'最高':<10} {'最低':<10} {'涨跌幅':<10}")
        print("-" * 70)

        for p in prices:
            change_str = f"{p['change_rate']:.2f}%" if p['change_rate'] is not None else "N/A"
            print(f"{p['trade_date']:<12} {p['close']:<10.2f} {change_str:<10} {p['open']:<10.2f} {p['high']:<10.2f} {p['low']:<10.2f} {int(p['volume'] or 0):<12,d}")
    else:
        print(f"未找到 {stock_code} 的价格数据")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="从 stock_daily_data 同步数据到 stock_price 表")
    parser.add_argument("stock_codes", nargs="*", help="股票代码")
    parser.add_argument("--sync", action="store_true", help="同步模式")
    parser.add_argument("--query", action="store_true", help="查询模式")
    parser.add_argument("--days", type=int, default=30, help="天数")
    args = parser.parse_args()

    if not args.stock_codes:
        parser.print_help()
        return

    if args.query:
        for code in args.stock_codes:
            query_price_table(code, args.days)
    elif args.sync:
        for code in args.stock_codes:
            sync_stock_to_price_table(code, args.days)


if __name__ == "__main__":
    main()
