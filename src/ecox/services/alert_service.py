"""告警服务"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db_session
from ..models import DataAlert
from ..validators.result import ValidationResult


class AlertService:
    """告警服务"""

    def __init__(self):
        pass

    def create_alert(
        self,
        stock_code: str,
        stock_name: Optional[str],
        alert_type: str,
        result: ValidationResult,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> DataAlert:
        """
        创建告警记录

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            alert_type: 告警类型
            result: 验证结果
            raw_data: 原始数据

        Returns:
            DataAlert: 创建的告警记录
        """
        # 构建告警消息
        messages = result.errors if result.errors else result.warnings
        alert_message = "; ".join(messages)

        # 获取交易日期
        trade_date = None
        if raw_data and "trade_date" in raw_data:
            trade_date = raw_data["trade_date"]

        alert = DataAlert(
            alert_level=result.alert_level,
            stock_code=stock_code,
            stock_name=stock_name,
            alert_type=alert_type,
            alert_message=alert_message,
            raw_data=raw_data,
            trade_date=trade_date,
            created_at=datetime.now(),
        )

        with get_db_session() as session:
            session.add(alert)
            session.commit()
            session.refresh(alert)

        return alert

    def create_alerts_batch(
        self,
        alerts: List[Dict[str, Any]]
    ) -> int:
        """
        批量创建告警记录

        Args:
            alerts: 告警数据列表

        Returns:
            int: 创建的告警数量
        """
        with get_db_session() as session:
            count = 0
            for alert_data in alerts:
                messages = alert_data["result"].errors or alert_data["result"].warnings
                alert_message = "; ".join(messages)

                raw_data = alert_data.get("raw_data")
                trade_date = None
                if raw_data and "trade_date" in raw_data:
                    trade_date = raw_data["trade_date"]

                alert = DataAlert(
                    alert_level=alert_data["result"].alert_level,
                    stock_code=alert_data["stock_code"],
                    stock_name=alert_data.get("stock_name"),
                    alert_type=alert_data["alert_type"],
                    alert_message=alert_message,
                    raw_data=raw_data,
                    trade_date=trade_date,
                    created_at=datetime.now(),
                )
                session.add(alert)
                count += 1

            session.commit()

        return count

    def get_unresolved_alerts(
        self,
        stock_code: Optional[str] = None,
        limit: int = 100,
    ) -> List[DataAlert]:
        """
        获取未解决的告警

        Args:
            stock_code: 股票代码过滤
            limit: 最多返回数量

        Returns:
            List[DataAlert]: 告警列表
        """
        with get_db_session() as session:
            query = session.query(DataAlert).filter(
                DataAlert.resolved == False
            )

            if stock_code:
                query = query.filter(DataAlert.stock_code == stock_code)

            alerts = query.order_by(
                DataAlert.created_at.desc()
            ).limit(limit).all()

            return alerts
