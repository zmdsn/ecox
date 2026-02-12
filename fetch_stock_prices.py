"""
从 akshare 获取股票每日价格并存储到数据库
使用新的 ORM 价格表和服务层
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import argparse
import logging
from datetime import datetime, date, timedelta
from typing import Dict
import time

import akshare as ak
import pandas as pd

from ecox.database import init_db
from ecox.services.price_service import PriceService
from ecox.services import StockService

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 请求间隔（秒）
CALL_INTERVAL = 0.5


def init_database():
    """初始化数据库表结构"""
    try:
        db = init_db()
        db.get_engine()
        db.create_all()
        logger.info("数据库表结构初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def fetch_akshare_prices(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """
    从 akshare 获取股票历史价格

    Args:
        stock_code: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)

    Returns:
        价格数据 DataFrame
    """
    try:
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="hfq"  # 后复权
        )

        if df.empty:
            logger.warning(f"股票 {stock_code} 未获取到数据")
            return pd.DataFrame()

        # 重命名列
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open_price',
            '收盘': 'close_price',
            '最高': 'high_price',
            '最低': 'low_price',
            '成交量': 'volume',
            '成交额': 'amount',
        })

        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date

        # 计算涨跌幅
        df = df.sort_values('trade_date')
        df['change_rate'] = df['close_price'].pct_change() * 100

        logger.info(f"获取 {stock_code} 数据: {len(df)} 条")
        return df

    except Exception as e:
        logger.error(f"获取 {stock_code} 数据失败: {e}")
        return pd.DataFrame()


def save_to_database(
    stock_code: str,
    df: pd.DataFrame,
) -> Dict[str, int]:
    """保存价格数据到数据库"""
    if df.empty:
        return {"saved": 0, "updated": 0, "total": 0}

    price_service = PriceService()

    # 转换为字典列表
    data_list = []
    for _, row in df.iterrows():
        data_list.append({
            "stock_code": stock_code,
            "trade_date": row['trade_date'],
            "close_price": float(row['close_price']) if pd.notna(row['close_price']) else None,
            "open_price": float(row['open_price']) if pd.notna(row['open_price']) else None,
            "high_price": float(row['high_price']) if pd.notna(row['high_price']) else None,
            "low_price": float(row['low_price']) if pd.notna(row['low_price']) else None,
            "volume": int(row['volume']) if pd.notna(row['volume']) else None,
            "amount": float(row['amount']) if pd.notna(row['amount']) else None,
            "change_rate": float(row['change_rate']) if pd.notna(row['change_rate']) else None,
        })

    # 保存到数据库
    result = price_service.save_price_data(data_list)

    logger.info(f"保存完成: 新增 {result['saved']} 条, 更新 {result['updated']} 条")
    return result


def update_stock_prices(
    stock_code: str,
    days: int = 365,
) -> Dict[str, int]:
    """
    更新股票价格数据

    Args:
        stock_code: 股票代码
        days: 获取最近N天的数据

    Returns:
        保存结果统计
    """
    logger.info(f"开始更新 {stock_code} 价格数据（最近 {days} 天）")

    # 计算日期范围
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # 获取数据
    df = fetch_akshare_prices(stock_code, start_date, end_date)

    if df.empty:
        logger.warning(f"未获取到 {stock_code} 的数据")
        return {"saved": 0, "updated": 0, "total": 0}

    # 保存到数据库
    result = save_to_database(stock_code, df)

    return result


def batch_update_stocks(
    stock_codes: list,
    days: int = 30,
) -> None:
    """批量更新多只股票的价格"""
    total_saved = 0
    total_updated = 0

    for i, code in enumerate(stock_codes):
        logger.info(f"处理 {i+1}/{len(stock_codes)}: {code}")

        result = update_stock_prices(code, days)
        total_saved += result['saved']
        total_updated += result['updated']

        # 请求间隔
        time.sleep(CALL_INTERVAL)

    logger.info(f"批量更新完成: 新增 {total_saved} 条, 更新 {total_updated} 条")


def query_stock_prices(
    stock_code: str,
    days: int = 30,
) -> None:
    """查询并显示股票价格"""
    price_service = PriceService()
    prices = price_service.get_latest_price(stock_code, days)

    if not prices:
        print(f"未找到股票 {stock_code} 的价格数据")
        return

    print(f"\n{'='*60}")
    print(f"股票: {stock_code}")
    print(f"最近 {len(prices)} 天价格")
    print(f"{'='*60}")

    print(f"{'日期':<12} {'收盘':<10} {'开盘':<10} {'最高':<10} {'最低':<10} {'涨跌幅':<10}")
    print("-" * 64)

    for p in prices:
        change_str = f"{p['change_rate']:.2f}%" if p['change_rate'] is not None else "N/A"
        print(f"{p['trade_date']:<12} {p['close']:<10.2f} {p['open']:<10.2f} {p['high']:<10.2f} {p['low']:<10.2f} {change_str:<10}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="股票价格数据管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取单只股票最近一年数据
  python fetch_stock_prices.py 600809 --update --days 365

  # 查询价格数据
  python fetch_stock_prices.py 600809 --query --days 30

  # 批量获取多只股票
  python fetch_stock_prices.py 600809 000001 600000 --batch --days 30
        """
    )

    parser.add_argument(
        "stock_codes",
        nargs="*",
        help="股票代码（可多个）"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="从 akshare 更新价格数据"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量模式"
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="查询已存储的价格数据"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="获取/查询最近N天数据（默认: 30）"
    )

    args = parser.parse_args()

    if not args.stock_codes:
        parser.print_help()
        return

    try:
        # 初始化数据库
        init_database()

        if args.query:
            # 查询模式
            for code in args.stock_codes:
                query_stock_prices(code, args.days)
        elif args.update:
            if args.batch:
                # 批量更新
                batch_update_stocks(args.stock_codes, args.days)
            else:
                # 单只更新
                for code in args.stock_codes:
                    update_stock_prices(code, args.days)
        else:
            print("请指定操作: --update 或 --query")
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        raise


if __name__ == "__main__":
    main()
