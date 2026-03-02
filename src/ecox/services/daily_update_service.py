"""
每日股票数据更新服务
统一的增量更新逻辑，支持断点续传和日志记录
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
import akshare as ak

from ecox.database import get_db_session
from ecox import models
from ecox.services import StockService
from ecox.services.alert_service import AlertService
from ..validators import CompositeValidator, PriceValidator, VolumeValidator

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 请求间隔（秒）
REQUEST_INTERVAL = 0.3


class DailyUpdateService:
    """每日股票数据更新服务"""

    def __init__(self):
        self.stock_service = StockService()
        # 新增：初始化验证器
        self.validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
        ])
        self.alert_service = AlertService()
        self.session = None  # 保留原有代码

    def get_stocks_need_update(
        self,
        days_behind: int = 1,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取需要更新的股票列表

        Args:
            days_behind: 距离最新交易日的天数差阈值
            limit: 最多返回的股票数量

        Returns:
            需要更新的股票列表，包含最后交易日期信息
        """
        with get_db_session() as session:
            # 获取最新交易日期（假设为昨天或今天）
            latest_possible_date = date.today()

            # 查询数据滞后的股票
            query = session.query(
                models.StockBasic.stock_code,
                models.StockBasic.stock_name
            ).outerjoin(
                models.StockPrice,
                models.StockBasic.stock_code == models.StockPrice.stock_code
            ).group_by(
                models.StockBasic.stock_code,
                models.StockBasic.stock_name
            )

            # 获取所有股票
            stocks = query.all()

            result = []
            for stock in stocks:
                stock_code = stock.stock_code

                # 获取该股票最新交易日期
                latest_price = session.query(
                    models.StockPrice.trade_date
                ).filter(
                    models.StockPrice.stock_code == stock_code
                ).order_by(
                    models.StockPrice.trade_date.desc()
                ).first()

                if latest_price:
                    latest_date = latest_price.trade_date
                    days_diff = (latest_possible_date - latest_date).days
                else:
                    # 没有任何价格数据
                    days_diff = 999

                if days_diff >= days_behind:
                    result.append({
                        "stock_code": stock_code,
                        "stock_name": stock.stock_name,
                        "latest_date": latest_price.trade_date if latest_price else None,
                        "days_diff": days_diff
                    })

            # 按 days_diff 降序排序（最需要更新的在前）
            result.sort(key=lambda x: x["days_diff"], reverse=True)

            if limit:
                result = result[:limit]

            return result

    def fetch_akshare_kline(
        self,
        stock_code: str,
        days: int = 90,
    ) -> List[Dict]:
        """
        从 akshare 获取K线数据

        Args:
            stock_code: 股票代码
            days: 获取最近N天的数据

        Returns:
            K线数据列表
        """
        try:
            # 计算日期范围
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

            # 调用 akshare
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="hfq"  # 后复权
            )

            if df.empty:
                return []

            # 转换为标准格式
            kline_data = []
            for _, row in df.iterrows():
                kline_data.append({
                    'stock_code': stock_code,
                    'trade_date': pd.to_datetime(row['日期']).date(),
                    'open_price': float(row['开盘']),
                    'close_price': float(row['收盘']),
                    'high_price': float(row['最高']),
                    'low_price': float(row['最低']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']) if '成交额' in row and pd.notna(row['成交额']) else None,
                })

            return kline_data

        except Exception as e:
            logger.error(f"获取 {stock_code} K线数据失败: {e}")
            return []

    def save_price_data(
        self,
        stock_code: str,
        data_list: List[Dict],
    ) -> Dict[str, int]:
        """
        保存价格数据到数据库（增量更新）

        只保存数据库中不存在的日期
        """
        with get_db_session() as session:
            saved_count = 0
            skipped_count = 0
            failed_count = 0

            # 新增：验证和告警收集
            alerts_to_create = []

            # 获取已存在的日期
            existing_dates = set()
            existing = session.query(
                models.StockPrice.trade_date
            ).filter(
                models.StockPrice.stock_code == stock_code,
                models.StockPrice.trade_date.in_([d['trade_date'] for d in data_list])
            ).all()

            for e in existing:
                existing_dates.add(e.trade_date)

            # 计算涨跌幅并保存
            sorted_data = sorted(data_list, key=lambda x: x['trade_date'])

            # 获取最后一个价格用于计算涨跌幅
            last_price = session.query(
                models.StockPrice.close_price
            ).filter(
                models.StockPrice.stock_code == stock_code
            ).order_by(
                models.StockPrice.trade_date.desc()
            ).first()

            prev_close = float(last_price.close_price) if last_price else None

            for item in sorted_data:
                # 跳过已存在的日期
                if item['trade_date'] in existing_dates:
                    skipped_count += 1
                    prev_close = item['close_price']
                    continue

                # 计算涨跌幅
                change_rate = None
                if prev_close is not None and prev_close > 0:
                    change_rate = ((item['close_price'] - prev_close) / prev_close) * 100

                # 添加 change_rate 到数据中
                item_with_change = item.copy()
                item_with_change['change_rate'] = change_rate

                # 新增：验证数据
                result = self.validator.validate(item_with_change)

                if not result.is_valid:
                    # 数据无效，记录告警
                    alerts_to_create.append({
                        "stock_code": stock_code,
                        "stock_name": item.get("stock_name"),
                        "alert_type": "data_validation_failed",
                        "result": result,
                        "raw_data": item_with_change,
                    })
                    failed_count += 1
                    logger.warning(f"{stock_code} {item['trade_date']}: 数据验证失败 - {result.errors}")
                    continue

                # 使用清洗后的数据或原始数据
                data_to_save = result.cleaned_data if result.cleaned_data else item_with_change

                price = models.StockPrice(
                    stock_code=stock_code,
                    trade_date=data_to_save['trade_date'],
                    close_price=data_to_save['close_price'],
                    open_price=data_to_save.get('open_price'),
                    high_price=data_to_save.get('high_price'),
                    low_price=data_to_save.get('low_price'),
                    volume=data_to_save.get('volume'),
                    amount=data_to_save.get('amount'),
                    change_rate=data_to_save.get('change_rate'),
                )
                session.add(price)
                saved_count += 1

                prev_close = data_to_save['close_price']

            session.commit()

            # 新增：批量创建告警
            if alerts_to_create:
                try:
                    self.alert_service.create_alerts_batch(alerts_to_create)
                except Exception as e:
                    logger.error(f"创建告警失败: {e}")

            return {
                "saved": saved_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "total": len(data_list),
            }

    def update_stock(
        self,
        stock_code: str,
        days: int = 90,
    ) -> Dict[str, int]:
        """
        更新单只股票的价格数据

        Args:
            stock_code: 股票代码
            days: 获取最近N天的数据

        Returns:
            更新结果统计
        """
        # 获取K线数据
        klines = self.fetch_akshare_kline(stock_code, days=days)

        if not klines:
            logger.warning(f"股票 {stock_code} 未获取到数据")
            return {"saved": 0, "skipped": 0, "total": 0}

        # 保存数据
        result = self.save_price_data(stock_code, klines)

        logger.info(f"{stock_code}: 新增 {result['saved']} 条, 跳过 {result['skipped']} 条")

        return result

    def batch_update(
        self,
        stock_codes: Optional[List[str]] = None,
        days: int = 90,
        max_count: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        批量更新股票价格数据

        Args:
            stock_codes: 股票代码列表，为空则自动获取需要更新的股票
            days: 获取最近N天的数据
            max_count: 最多更新的股票数量

        Returns:
            更新结果统计
        """
        # 如果没有指定股票，获取需要更新的股票
        if not stock_codes:
            stocks_need_update = self.get_stocks_need_update(days_behind=1, limit=max_count)
            stock_codes = [s["stock_code"] for s in stocks_need_update]

        if not stock_codes:
            logger.info("没有需要更新的股票")
            return {"saved": 0, "updated": 0, "failed": 0, "total": 0}

        logger.info(f"开始批量更新 {len(stock_codes)} 只股票的数据")

        total_saved = 0
        total_skipped = 0
        failed_count = 0
        failed_codes = []

        for i, code in enumerate(stock_codes):
            try:
                logger.info(f"处理 {i+1}/{len(stock_codes)}: {code}")

                result = self.update_stock(code, days)
                total_saved += result['saved']
                total_skipped += result['skipped']

                if result['saved'] == 0 and result['skipped'] == 0:
                    failed_codes.append(code)
                    failed_count += 1

                # 每100只打印进度
                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i+1}/{len(stock_codes)}, 新增: {total_saved}, 跳过: {total_skipped}, 失败: {failed_count}")

                # 请求间隔
                time.sleep(REQUEST_INTERVAL)

            except KeyboardInterrupt:
                logger.info("用户中断")
                break
            except Exception as e:
                logger.error(f"处理 {code} 时出错: {e}")
                failed_codes.append(code)
                failed_count += 1
                time.sleep(REQUEST_INTERVAL)

        # 记录更新日志
        self._log_update(total_saved, total_skipped, failed_count, failed_codes)

        logger.info("="*60)
        logger.info("批量更新完成!")
        logger.info(f"总计: 新增 {total_saved} 条, 跳过 {total_skipped} 条, 失败 {failed_count} 只")

        if failed_codes:
            logger.info(f"失败股票代码（前20个）: {failed_codes[:20]}")

        return {
            "saved": total_saved,
            "skipped": total_skipped,
            "failed": failed_count,
            "total": total_saved + total_skipped,
        }

    def _log_update(
        self,
        saved: int,
        skipped: int,
        failed: int,
        failed_codes: List[str],
    ):
        """记录更新日志"""
        try:
            with get_db_session() as session:
                log = models.UpdateLog(
                    run_time=datetime.now(),
                    success_count=saved + skipped,
                    failed_count=failed,
                    new_rows_count=saved,
                    error_message=",".join(failed_codes[:100]) if failed_codes else None,
                )
                session.add(log)
                session.commit()
        except Exception as e:
            logger.error(f"记录更新日志失败: {e}")

    def update_today(self, stock_codes: Optional[List[str]] = None):
        """
        更新今日数据

        Args:
            stock_codes: 要更新的股票列表，为空则更新所有需要更新的股票
        """
        logger.info("开始更新今日股票数据...")

        # 初始化数据库
        from ecox.database import init_db
        db = init_db()
        db.create_all()

        result = self.batch_update(stock_codes=stock_codes, days=7)

        logger.info(f"今日更新完成: {result}")

        return result


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="每日股票数据更新服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 更新所有需要更新的股票
  python daily_update_service.py --update

  # 更新指定股票
  python daily_update_service.py --update --codes 600809 000001

  # 查看需要更新的股票
  python daily_update_service.py --check
        """
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="执行更新"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查需要更新的股票"
    )
    parser.add_argument(
        "--codes",
        nargs="*",
        help="股票代码列表"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="最多更新的股票数量"
    )

    args = parser.parse_args()

    service = DailyUpdateService()

    if args.check:
        stocks = service.get_stocks_need_update(days_behind=1)
        print(f"\n需要更新的股票数量: {len(stocks)}")
        print(f"{'股票代码':<10} {'股票名称':<10} {'最后日期':<12} {'滞后天数':<8}")
        print("-" * 50)
        for s in stocks[:20]:
            latest_str = s['latest_date'].isoformat() if s['latest_date'] else "无数据"
            print(f"{s['stock_code']:<10} {s['stock_name']:<10} {latest_str:<12} {s['days_diff']:<8}")
        if len(stocks) > 20:
            print(f"... 还有 {len(stocks) - 20} 只股票")

    elif args.update:
        service.update_today(stock_codes=args.codes)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
