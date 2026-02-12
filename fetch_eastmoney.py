"""
使用东方财富 API 直接获取股票数据
不依赖 akshare，更稳定
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import argparse
import logging
import time
from datetime import datetime, date, timedelta
from typing import Dict, List
import requests

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

# 请求间隔
REQUEST_INTERVAL = 0.3


def fetch_eastmoney_kline(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    count: int = 100,
) -> List[Dict]:
    """
    从东方财富获取K线数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        count: 获取条数

    Returns:
        K线数据列表
    """
    # 东方财富K线接口
    url = "http://push2.eastmoney.com/api/qt/stock/klt.kline/get"

    # 构建参数
    secid = stock_code

    # 判断市场
    if stock_code.startswith("6"):
        secid = f"1.{stock_code}"  # 上海
    elif stock_code.startswith("0") or stock_code.startswith("3"):
        secid = f"0.{stock_code}"  # 深圳
    else:
        secid = f"1.{stock_code}"  # 默认上海

    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15",
        "klt": 1,  # 日K线
        "fqt": 1,  # 前复权
        "end": end_date or "20500101",
        "lmt": count,
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(f"请求失败: {response.status_code}")
            return []

        data = response.json()

        if data.get("rc") != 0:
            logger.error(f"API返回错误: {data.get('rc')}")
            return []

        kline_data = []
        raw_data = data.get('data', {}).get('s2n', {})

        for item in raw_data:
            if item.get('symbol') == stock_code:
                klines = item.get('kline', [])
                for k in klines:
                    # 解析K线数据
                    kline_data.append({
                        'stock_code': stock_code,
                        'trade_date': datetime.strptime(k[0], "%Y-%m-%d %H:%M:%S").date(),
                        'open_price': float(k[1]),
                        'close_price': float(k[2]),
                        'high_price': float(k[3]),
                        'low_price': float(k[4]),
                        'volume': int(k[5]) if len(k) > 5 else 0,
                        'amount': float(k[6]) if len(k) > 6 else None,
                    })

        logger.info(f"获取到 {len(kline_data)} 条K线数据")
        return kline_data[:count] if count > 0 else kline_data

    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return []


def fetch_eastmoney_quote(
    stock_codes: List[str],
) -> Dict[str, Dict]:
    """
    获取实时行情

    Returns:
        {股票代码: 行情数据}
    """
    url = "http://push2.eastmoney.com/api/qt/stock/get"

    params = {
        "secid": ",".join([f"1.{c}" if c.startswith("6") else f"0.{c}" for c in stock_codes]),
        "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58",
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(f"请求失败: {response.status_code}")
            return {}

        data = response.json()

        if data.get("rc") != 0:
            logger.error(f"API返回错误: {data.get('rc')}")
            return {}

        quote_data = {}
        raw_data = data.get('data', {}).get('diff', {})

        for item in raw_data:
            code = item.get('symbol', '').replace('sh', '').replace('sz', '')
            quote_data[code] = {
                'stock_code': code,
                'price': float(item.get('f43', 0)),  # 最新价
                'change': float(item.get('f44', 0)),   # 涨跌额
                'change_rate': float(item.get('f45', 0)),  # 涨跌幅
                'volume': int(item.get('f47', 0)),    # 成交量(手)
                'turnover': float(item.get('f48', 0)),  # 成交额(万)
                'high': float(item.get('f50', 0)),    # 最高
                'low': float(item.get('f51', 0)),     # 最低
                'open': float(item.get('f46', 0)),    # 今开
                'pre_close': float(item.get('f60', 0)),  # 昨收
            }

        logger.info(f"获取到 {len(quote_data)} 只股票的实时行情")
        return quote_data

    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        return {}


def save_price_data(
    stock_code: str,
    data_list: List[Dict],
) -> Dict[str, int]:
    """保存价格数据到数据库"""
    price_service = PriceService()

    # 添加 trade_date 并计算涨跌幅
    processed_data = []
    prev_close = None

    # 排序确保按日期
    sorted_data = sorted(data_list, key=lambda x: x['trade_date'])

    for item in sorted_data:
        close_price = item['close_price']
        change_rate = None

        if prev_close is not None:
            change_rate = ((close_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0

        processed_data.append({
            **item,
            'change_rate': change_rate,
        })

        prev_close = close_price

    result = price_service.save_price_data(processed_data)
    logger.info(f"保存完成: 新增 {result['saved']} 条, 更新 {result['updated']} 条")

    return result


def batch_fetch_and_save(
    stock_codes: List[str],
    days: int = 90,
) -> Dict[str, int]:
    """
    批量获取并保存股票价格

    Args:
        stock_codes: 股票代码列表
        days: 获取天数
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    total_saved = 0
    total_updated = 0

    for i, code in enumerate(stock_codes):
        logger.info(f"处理 {i+1}/{len(stock_codes)}: {code}")

        # 获取K线数据
        klines = fetch_eastmoney_kline(code, start_date, end_date, count=days*2)

        if klines:
            result = save_price_data(code, klines)
            total_saved += result['saved']
            total_updated += result['updated']

        # 请求间隔
        time.sleep(REQUEST_INTERVAL)

    logger.info(f"批量获取完成: 新增 {total_saved} 条, 更新 {total_updated} 条")

    return {
        "saved": total_saved,
        "updated": total_updated,
        "total": total_saved + total_updated,
    }


def query_and_display(
    stock_code: str,
    days: int = 30,
) -> None:
    """查询并显示价格数据"""
    price_service = PriceService()
    prices = price_service.get_latest_price(stock_code, days)

    if not prices:
        print(f"未找到股票 {stock_code} 的价格数据")
        return

    print(f"\n{'='*70}")
    print(f"股票: {stock_code}")
    print(f"最近 {len(prices)} 天价格数据")
    print(f"{'='*70}")

    print(f"{'日期':<12} {'收盘':<10} {'涨跌幅':<10} {'开盘':<10} {'最高':<10} {'最低':<10} {'成交量':<12}")
    print("-" * 70)

    for p in prices:
        change_str = f"{p['change_rate']:.2f}%" if p['change_rate'] is not None else "N/A"
        print(f"{p['trade_date']:<12} {p['close']:<10.2f} {change_str:<10} {p['open']:<10.2f} {p['high']:<10.2f} {p['low']:<10.2f} {int(p['volume'] or 0):<12,d}")

    print("-" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="东方财富 API 数据获取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取并保存价格数据
  python fetch_eastmoney.py 600809 --fetch --days 90

  # 查询价格数据
  python fetch_eastmoney.py 600809 --query --days 30

  # 批量获取多只股票
  python fetch_eastmoney.py 600809 000001 600000 --batch --days 30
        """
    )

    parser.add_argument(
        "stock_codes",
        nargs="*",
        help="股票代码（可多个）"
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="从东方财富获取并保存数据"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量模式"
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="查询模式：查询 stock_price 表"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="获取/查询最近N天数据（默认: 30）"
    )
    parser.add_argument(
        "--quote",
        action="store_true",
        help="获取实时行情"
    )

    args = parser.parse_args()

    if not args.stock_codes:
        parser.print_help()
        return

    try:
        # 初始化数据库
        init_db()

        if args.query:
            for code in args.stock_codes:
                query_and_display(code, args.days)
        elif args.quote:
            quotes = fetch_eastmoney_quote(args.stock_codes)
            for code, data in quotes.items():
                print(f"\n{code}:")
                print(f"  最新价: {data['price']}")
                print(f"  涨跌幅: {data['change_rate']}%")
                print(f"  成交量: {data['volume']} 手")
        elif args.fetch:
            if args.batch:
                batch_fetch_and_save(args.stock_codes, args.days)
            else:
                for code in args.stock_codes:
                    result = batch_fetch_and_save([code], args.days)
        else:
            print("请指定操作: --fetch, --query 或 --quote")
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        raise


if __name__ == "__main__":
    main()
