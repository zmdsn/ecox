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
            # 转换数据格式（如果是新浪数据，从DataFrame转为dict）
            if fresh_data.get('source') == 'sina':
                fresh_data = self._convert_sina_data(fresh_data)

            # Step 4: 存储到数据库（仅支持东方财富格式）
            if fresh_data.get('source') == 'eastmoney':
                self._save_to_database(fresh_data)
            else:
                logger.info(f"Skipping database save for {fresh_data.get('source')} data (format not supported)")

            # 更新内存缓存
            self._update_memory_cache(formatted_code, report_date, fresh_data)

            return fresh_data

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
            f"数据源接口异常：无法获取 {formatted_code} 的财务数据。akshare 接口当前不可用（可能是东方财富网页结构变化）。",
            details={
                "stock_code": stock_code,
                "report_date": report_date,
                "reason": "akshare library bug - 东方财富网页结构变化",
                "suggestion": "建议使用其他数据源或等待 akshare 更新"
            }
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
        """从 akshare 获取数据（带并发控制）

        优先使用同花顺接口，如果失败则尝试东方财富接口
        """
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
                logger.info(f"Downloading financial data for {stock_code}")

                # 去掉前缀用于 akshare
                ak_code = stock_code[2:]

                # 优先尝试新浪财经接口（数据完整且稳定）
                data = self._fetch_from_sina(ak_code, stock_code)
                if data:
                    return data

                # 如果新浪失败，尝试同花顺接口
                logger.info(f"Sina interface failed, trying THS for {stock_code}")
                data = self._fetch_from_ths(ak_code, stock_code)
                if data:
                    return data

                # 如果同花顺也失败，尝试东方财富接口（可能失效）
                logger.info(f"THS interface failed, trying Eastmoney for {stock_code}")
                data = self._fetch_from_eastmoney(ak_code, stock_code)
                if data:
                    return data

                return None

        except Exception as e:
            logger.error(f"Error fetching from akshare: {e}")
            return None
        finally:
            self._download_queue.discard(task_id)

    def _fetch_from_sina(self, ak_code: str, stock_code: str) -> dict[str, Any] | None:
        """从新浪财经接口获取财务数据（推荐）"""
        try:
            import akshare as ak

            logger.info(f"Fetching from Sina (新浪) for {ak_code}")

            # 并行获取三大报表
            profit_df = ak.stock_financial_report_sina(stock=stock_code.lower(), symbol="利润表")
            balance_df = ak.stock_financial_report_sina(stock=stock_code.lower(), symbol="资产负债表")
            cashflow_df = ak.stock_financial_report_sina(stock=stock_code.lower(), symbol="现金流量表")

            # 获取股票名称
            stock_name = 'Unknown'

            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'profit_df': profit_df,
                'balance_df': balance_df,
                'cashflow_df': cashflow_df,
                'source': 'sina',
                'fetch_time': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error fetching from Sina: {e}")
            return None

    def _convert_sina_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """转换新浪数据格式为标准格式

        Args:
            data: 新浪接口返回的原始数据

        Returns:
            转换后的标准格式数据
        """
        profit_df = data.get('profit_df')
        balance_df = data.get('balance_df')
        cashflow_df = data.get('cashflow_df')

        # 提取最新报告日期
        report_date = None
        report_type = 'Unknown'
        if profit_df is not None and not profit_df.empty:
            latest_date_str = profit_df.iloc[0]['报告日']
            try:
                # 新浪日期格式：20250930 -> 2025-09-30
                if len(latest_date_str) == 8:
                    year = latest_date_str[:4]
                    month = latest_date_str[4:6]
                    day = latest_date_str[6:8]
                    report_date = f"{year}-{month}-{day}"
                else:
                    report_date = latest_date_str

                # 推断报告类型
                month_int = int(latest_date_str[4:6]) if len(latest_date_str) >= 6 else 0
                if month_int == 3:
                    report_type = 'Q1'
                elif month_int == 6:
                    report_type = 'Q2'
                elif month_int == 9:
                    report_type = 'Q3'
                elif month_int == 12:
                    report_type = 'Q4'
            except:
                pass

        # 字段名映射：中文字段名 -> 英文字段名
        profit_field_mapping = {
            '净利润': 'net_profit',
            '营业总收入': 'total_revenue',
            '营业收入': 'revenue',
            '财务费用': 'interest_expense',
            '利息费用': 'interest_expense',
            '研发费用': 'rd_expenses',
            '销售费用': 'selling_expenses',
            '管理费用': 'admin_expenses',
            '营业成本': 'operating_cost',
            '营业利润': 'operating_profit',
            '利润总额': 'total_profit',
        }

        balance_field_mapping = {
            '资产总计': 'total_assets',
            '负债合计': 'total_liabilities',
            '所有者权益(或股东权益)合计': 'total_equity',
            '流动资产合计': 'current_assets',
            '流动负债合计': 'current_liabilities',
            '固定资产净额': 'fixed_assets',
            '货币资金': 'cash',
            '存货': 'inventory',
        }

        cashflow_field_mapping = {
            '经营活动产生的现金流量净额': 'operating_cash_flow',
            '投资活动产生的现金流量净额': 'investing_cash_flow',
            '筹资活动产生的现金流量净额': 'financing_cash_flow',
            '购建固定资产、无形资产和其他长期资产所支付的现金': 'capex',
            '现金及现金等价物净增加额': 'net_cash_increase',
            '期末现金及现金等价物余额': 'cash_balance',
        }

        # 转换利润表
        profit_sheet = {}
        if profit_df is not None and not profit_df.empty:
            row = profit_df.iloc[0]
            raw_dict = row.to_dict()
            # 应用字段映射
            for cn_name, en_name in profit_field_mapping.items():
                if cn_name in raw_dict:
                    profit_sheet[en_name] = raw_dict[cn_name]
            # 保留原始字段
            profit_sheet.update(raw_dict)

        # 转换资产负债表
        balance_sheet = {}
        if balance_df is not None and not balance_df.empty:
            row = balance_df.iloc[0]
            raw_dict = row.to_dict()
            # 应用字段映射
            for cn_name, en_name in balance_field_mapping.items():
                if cn_name in raw_dict:
                    balance_sheet[en_name] = raw_dict[cn_name]
            # 保留原始字段
            balance_sheet.update(raw_dict)

        # 转换现金流量表
        cash_flow_sheet = {}
        if cashflow_df is not None and not cashflow_df.empty:
            row = cashflow_df.iloc[0]
            raw_dict = row.to_dict()
            # 应用字段映射
            for cn_name, en_name in cashflow_field_mapping.items():
                if cn_name in raw_dict:
                    cash_flow_sheet[en_name] = raw_dict[cn_name]
            # 保留原始字段
            cash_flow_sheet.update(raw_dict)

        return {
            'stock_code': data['stock_code'],
            'stock_name': data.get('stock_name', 'Unknown'),
            'report_date': report_date,
            'report_type': report_type,
            'profit_sheet': profit_sheet,
            'balance_sheet': balance_sheet,
            'cash_flow_sheet': cash_flow_sheet,
            'source': data['source'],
            'fetch_time': data.get('fetch_time')
        }

    def _fetch_from_eastmoney(self, ak_code: str, stock_code: str) -> dict[str, Any] | None:
        """从东方财富接口获取财务数据（原有方法，可能失效）"""
        try:
            import akshare as ak

            logger.info(f"Fetching from Eastmoney for {ak_code}")

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
                'source': 'eastmoney',
                'fetch_time': datetime.now()
            }

        except Exception as e:
            error_msg = str(e)
            if "'NoneType' object is not subscriptable" in error_msg:
                logger.error(f"Eastmoney interface unavailable: 东方财富网页结构已变化")
            else:
                logger.error(f"Error fetching from Eastmoney: {e}")
            return None

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
