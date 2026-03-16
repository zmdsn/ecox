"""懒加载服务 - 自动获取和缓存财务数据"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Any
import threading
import pandas as pd

from ecox.utils import code_format
from ecox.database import get_db_session
from ecox.exceptions import ExternalDataSourceError

logger = logging.getLogger(__name__)


class LazyLoadingService:
    """
    懒加载服务

    功能:
    - 自动检查缓存（内存、数据库）
    - 从 akshare 下载缺失数据
    - 自动存储到数据库
    - 并发控制，防止重复下载
    """

    # 缓存过期时间（天）
    CACHE_EXPIRY_DAYS = {
        'Q1': 120,    # 一季报：4个月后过期
        'Q2': 120,    # 中报：4个月后过期
        'Q3': 120,    # 三季报：4个月后过期
        'Q4': 180,    # 年报：6个月后过期
    }

    def __init__(self):
        """初始化懒加载服务"""
        self._memory_cache: dict[str, Any] = {}
        self._downloading = threading.Lock()
        self._download_queue: set[str] = set()

    def get_financial_data(
        self,
        stock_code: str,
        report_date: str | None = None,
        force_refresh: bool = False
    ) -> dict[str, Any]:
        """
        获取财务数据（懒加载模式）

        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，None 表示最新）
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            包含财务数据的字典

        Raises:
            ExternalDataSourceError: 无法获取数据
        """
        formatted_code = code_format(stock_code)

        logger.info(f"Lazy loading financial data for {formatted_code}")

        # Step 1: 检查内存缓存
        if not force_refresh:
            cached = self._check_memory_cache(formatted_code, report_date)
            if cached:
                logger.debug("Memory cache hit")
                return cached

        # Step 2: 检查数据库
        db_data = self._fetch_from_database(formatted_code, report_date)

        if db_data and not force_refresh:
            if self._is_data_fresh(db_data):
                logger.info(f"Database hit for {formatted_code}")
                # 更新内存缓存
                self._update_memory_cache(formatted_code, report_date, db_data)
                return db_data
            else:
                logger.info(f"Data expired for {formatted_code}, refreshing...")

        # Step 3: 从 akshare 下载
        logger.info(f"Fetching from akshare for {formatted_code}")
        fresh_data = self._fetch_from_akshare(formatted_code)

        if fresh_data:
            # Step 4: 存储到数据库
            self._save_to_database(fresh_data)

            # 更新内存缓存
            self._update_memory_cache(formatted_code, report_date, fresh_data)

            return fresh_data

        # 如果下载失败，返回数据库中的旧数据（如果有）
        if db_data:
            logger.warning(
                f"Failed to fetch fresh data, using cached data for {formatted_code}"
            )
            return db_data

        raise ExternalDataSourceError(
            f"Unable to fetch financial data for {formatted_code}",
            details={"stock_code": stock_code, "report_date": report_date}
        )

    def _check_memory_cache(
        self,
        stock_code: str,
        report_date: str | None
    ) -> dict[str, Any] | None:
        """检查内存缓存"""
        cache_key = self._get_cache_key(stock_code, report_date)
        return self._memory_cache.get(cache_key)

    def _update_memory_cache(
        self,
        stock_code: str,
        report_date: str | None,
        data: dict[str, Any]
    ) -> None:
        """更新内存缓存"""
        cache_key = self._get_cache_key(stock_code, report_date)
        self._memory_cache[cache_key] = data

    def _get_cache_key(self, stock_code: str, report_date: str | None) -> str:
        """生成缓存键"""
        return f"{stock_code}_{report_date or 'latest'}"

    def _fetch_from_database(
        self,
        stock_code: str,
        report_date: str | None
    ) -> dict[str, Any] | None:
        """从数据库获取数据"""
        try:
            from ecox.models import StockProfitSheet
            from sqlalchemy import desc

            with get_db_session() as session:
                query = session.query(StockProfitSheet).filter(
                    StockProfitSheet.stock_code == stock_code
                )

                if report_date:
                    report_dt = datetime.fromisoformat(report_date) if isinstance(report_date, str) else report_date
                    query = query.filter(StockProfitSheet.report_date == report_dt)

                record = query.order_by(desc(StockProfitSheet.report_date)).first()

                if not record:
                    return None

                return {
                    'stock_code': stock_code,
                    'stock_name': record.stock_name,
                    'report_date': record.report_date,
                    'report_type': record.report_type,
                    'profit_sheet': record.extra_data or {},
                    'source': 'database',
                    'fetch_time': datetime.now()
                }

        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return None

    def _fetch_from_akshare(self, stock_code: str) -> dict[str, Any] | None:
        """从 akshare 获取数据（带并发控制）"""
        task_id = stock_code

        # 防止重复下载
        if task_id in self._download_queue:
            logger.info(f"Already downloading {stock_code}, waiting...")
            import time
            for _ in range(30):
                time.sleep(1)
                if task_id not in self._download_queue:
                    return self._fetch_from_database(stock_code, None)
            return None

        self._download_queue.add(task_id)

        try:
            with self._downloading:
                logger.info(f"Downloading financial data for {stock_code} from akshare")

                import akshare as ak

                # 去掉前缀用于 akshare
                ak_code = stock_code[2:]

                # 并行下载三大报表
                profit_df = ak.stock_profit_sheet_by_report_em(symbol=ak_code)
                balance_df = ak.stock_balance_sheet_by_report_em(symbol=ak_code)
                cashflow_df = ak.stock_cash_flow_sheet_by_report_em(symbol=ak_code)

                # 获取股票名称
                try:
                    stock_info = ak.stock_individual_info_em(symbol=ak_code)
                    stock_name = stock_info.get('股票简称', 'Unknown')
                except:
                    stock_name = 'Unknown'

                return {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'profit_df': profit_df,
                    'balance_df': balance_df,
                    'cashflow_df': cashflow_df,
                    'source': 'akshare',
                    'fetch_time': datetime.now()
                }

        except Exception as e:
            logger.error(f"Error fetching from akshare: {e}")
            return None
        finally:
            self._download_queue.discard(task_id)

    def _save_to_database(self, data: dict[str, Any]) -> bool:
        """保存数据到数据库"""
        try:
            from ecox.models import StockProfitSheet

            with get_db_session() as session:
                if 'profit_df' in data:
                    count = 0
                    for _, row in data['profit_df'].iterrows():
                        report_dt = pd.to_datetime(row['REPORT_DATE'])

                        record = session.query(StockProfitSheet).filter_by(
                            stock_code=data['stock_code'],
                            report_date=report_dt
                        ).first()

                        if not record:
                            record = StockProfitSheet(
                                stock_code=data['stock_code'],
                                stock_name=data['stock_name'],
                                report_date=report_dt,
                                report_type=self._infer_report_type(row['REPORT_DATE']),
                                extra_data=row.to_dict()
                            )
                            session.add(record)
                        else:
                            # 更新 extra_data
                            record.extra_data = row.to_dict()

                        count += 1

                    session.commit()
                    logger.info(f"Saved {count} profit records to database")

                return True

        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False

    def _is_data_fresh(self, data: dict[str, Any]) -> bool:
        """检查数据是否过期"""
        report_date = data.get('report_date')
        report_type = data.get('report_type')

        if not report_date:
            return False

        if isinstance(report_date, str):
            report_date = datetime.fromisoformat(report_date)

        # 计算数据年龄
        age = datetime.now() - report_date
        max_age = timedelta(days=self.CACHE_EXPIRY_DAYS.get(report_type, 90))

        return age <= max_age

    def _infer_report_type(self, date_str) -> str:
        """从日期推断报告类型"""
        if isinstance(date_str, str):
            parts = date_str.split('-')
            if len(parts) >= 2:
                month = int(parts[1])
            else:
                return 'Unknown'
        else:
            month = date_str.month if hasattr(date_str, 'month') else 0

        if month == 3:
            return 'Q1'
        elif month == 6:
            return 'Q2'
        elif month == 9:
            return 'Q3'
        elif month == 12:
            return 'Q4'
        return 'Unknown'

    def invalidate_cache(self, stock_code: str | None = None) -> None:
        """
        使缓存失效

        Args:
            stock_code: 特定股票代码，None 表示清除所有缓存
        """
        if stock_code:
            keys_to_remove = [
                k for k in self._memory_cache.keys()
                if k.startswith(stock_code)
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]

            # 清除 LRU 缓存
            if hasattr(self.get_financial_data, 'cache_clear'):
                self.get_financial_data.cache_clear()
        else:
            self._memory_cache.clear()
            if hasattr(self.get_financial_data, 'cache_clear'):
                self.get_financial_data.cache_clear()

        logger.info(f"Cache invalidated for {stock_code or 'all stocks'}")
