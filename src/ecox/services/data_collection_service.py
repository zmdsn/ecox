"""
数据采集服务层
负责从外部数据源采集数据并存储到数据库
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging

from ..database import get_db_session
from .. import models

logger = logging.getLogger(__name__)


class DataCollectionService:
    """数据采集服务"""

    def save_realtime_data(self, data_list: List[Dict]) -> Dict[str, int]:
        """
        保存实时行情数据

        Args:
            data_list: 实时行情数据列表
                [{
                    "stock_code": "000001",
                    "stock_name": "平安银行",
                    "latest_price": 10.50,
                    "price_change": 0.50,
                    "price_change_rate": 5.00,
                    "volume": 1000000,
                    "turnover": 10500000,
                    "high_price": 10.80,
                    "low_price": 10.20,
                    "open_price": 10.30,
                    "pre_close_price": 10.00,
                }]

        Returns:
            统计信息 {"success": int, "failed": int}
        """
        success_count = 0
        failed_count = 0

        try:
            with get_db_session() as session:
                now = datetime.utcnow()

                for data in data_list:
                    try:
                        # 检查是否存在今日数据
                        existing = (
                            session.query(models.StockRealTime)
                            .filter(
                                models.StockRealTime.stock_code == data["stock_code"],
                                models.StockRealTime.update_time >= date.today(),
                            )
                            .first()
                        )

                        record_data = {
                            **data,
                            "update_time": now,
                        }

                        if existing:
                            # 更新现有记录
                            for key, value in record_data.items():
                                setattr(existing, key, value)
                        else:
                            # 创建新记录
                            record = models.StockRealTime(**record_data)
                            session.add(record)

                        success_count += 1

                    except Exception as e:
                        logger.error(f"保存实时数据失败: {data.get('stock_code')}, 错误: {e}")
                        failed_count += 1

                session.commit()

        except Exception as e:
            logger.error(f"批量保存实时数据失败: {e}")
            failed_count = len(data_list)

        return {"success": success_count, "failed": failed_count}

    def save_daily_data(self, data_list: List[Dict]) -> Dict[str, int]:
        """
        保存日线数据

        Args:
            data_list: 日线数据列表
                [{
                    "stock_code": "000001",
                    "trade_date": "2024-01-01",
                    "open": 10.30,
                    "close": 10.50,
                    "high": 10.80,
                    "low": 10.20,
                    "volume": 1000000,
                    "amount": 10500000,
                    "adjust_flag": "qfq",
                }]

        Returns:
            统计信息 {"success": int, "failed": int, "new": int}
        """
        success_count = 0
        failed_count = 0
        new_count = 0

        try:
            with get_db_session() as session:
                now = datetime.utcnow()

                for data in data_list:
                    try:
                        # 检查是否已存在
                        existing = (
                            session.query(models.StockDailyData)
                            .filter(
                                models.StockDailyData.stock_code == data["stock_code"],
                                models.StockDailyData.trade_date == data.get("trade_date"),
                                models.StockDailyData.adjust_flag == data.get("adjust_flag", "qfq"),
                            )
                            .first()
                        )

                        record_data = {
                            **data,
                            "update_time": now,
                        }

                        if existing:
                            # 更新现有记录
                            for key, value in record_data.items():
                                setattr(existing, key, value)
                        else:
                            # 创建新记录
                            record = models.StockDailyData(**record_data)
                            session.add(record)
                            new_count += 1

                        success_count += 1

                    except Exception as e:
                        logger.error(f"保存日线数据失败: {data.get('stock_code')}, 错误: {e}")
                        failed_count += 1

                session.commit()

        except Exception as e:
            logger.error(f"批量保存日线数据失败: {e}")
            failed_count = len(data_list)

        return {"success": success_count, "failed": failed_count, "new": new_count}

    def save_financial_report(
        self,
        report_type: str,
        data_list: List[Dict],
    ) -> Dict[str, int]:
        """
        保存财务报表数据

        Args:
            report_type: 报表类型 (profit/balance/cashflow)
            data_list: 财务数据列表

        Returns:
            统计信息
        """
        success_count = 0
        failed_count = 0

        try:
            with get_db_session() as session:
                now = datetime.utcnow()

                model_map = {
                    "profit": models.StockProfitSheet,
                    "balance": models.StockBalanceSheet,
                    "cashflow": models.StockCashFlowSheet,
                }

                Model = model_map.get(report_type)
                if not Model:
                    raise ValueError(f"不支持的报表类型: {report_type}")

                for data in data_list:
                    try:
                        # 检查是否已存在
                        existing = (
                            session.query(Model)
                            .filter(
                                Model.stock_code == data["stock_code"],
                                Model.report_date == data["report_date"],
                                Model.report_type == data.get("report_type", "annual"),
                            )
                            .first()
                        )

                        record_data = {
                            **data,
                            "create_time": now,
                        }

                        if existing:
                            for key, value in record_data.items():
                                setattr(existing, key, value)
                        else:
                            record = Model(**record_data)
                            session.add(record)

                        success_count += 1

                    except Exception as e:
                        logger.error(f"保存财务报表失败: {data.get('stock_code')}, 错误: {e}")
                        failed_count += 1

                session.commit()

        except Exception as e:
            logger.error(f"批量保存财务报表失败: {e}")
            failed_count = len(data_list)

        return {"success": success_count, "failed": failed_count}

    def log_update(
        self,
        success_count: int,
        failed_count: int,
        new_rows_count: int,
        error_message: Optional[str] = None,
    ) -> None:
        """记录更新日志"""
        try:
            with get_db_session() as session:
                log = models.UpdateLog(
                    run_time=datetime.utcnow(),
                    success_count=success_count,
                    failed_count=failed_count,
                    new_rows_count=new_rows_count,
                    error_message=error_message,
                )
                session.add(log)
                session.commit()

        except Exception as e:
            logger.error(f"记录更新日志失败: {e}")

    def get_latest_update_log(self) -> Optional[Dict[str, Any]]:
        """获取最新的更新日志"""
        try:
            with get_db_session() as session:
                log = (
                    session.query(models.UpdateLog)
                    .order_by(models.UpdateLog.run_time.desc())
                    .first()
                )

                if log:
                    return {
                        "run_time": log.run_time.isoformat() if log.run_time else None,
                        "success_count": log.success_count,
                        "failed_count": log.failed_count,
                        "new_rows_count": log.new_rows_count,
                        "error_message": log.error_message,
                    }

        except Exception as e:
            logger.error(f"获取更新日志失败: {e}")

        return None

    def get_update_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取更新日志列表"""
        try:
            with get_db_session() as session:
                logs = (
                    session.query(models.UpdateLog)
                    .order_by(models.UpdateLog.run_time.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "run_time": log.run_time.isoformat() if log.run_time else None,
                        "success_count": log.success_count,
                        "failed_count": log.failed_count,
                        "new_rows_count": log.new_rows_count,
                        "error_message": log.error_message,
                    }
                    for log in logs
                ]

        except Exception as e:
            logger.error(f"获取更新日志列表失败: {e}")

        return []
