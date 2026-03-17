"""行情数据工具"""
from typing import Dict, Any
from .base import Tool
from ...utils import code_format


class MarketDataTool(Tool):
    """行情数据工具"""

    @property
    def name(self) -> str:
        return "market_data"

    @property
    def description(self) -> str:
        return "查询股票实时行情数据，包括股价、涨跌幅、成交量等"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                }
            },
            "required": ["stock_code"]
        }

    async def execute(self, stock_code: str = None, **kwargs) -> Dict[str, Any]:
        """获取行情数据（智能数据优先策略）

        策略：
        1. 优先使用今天采集的实时数据（即使几小时前）
        2. 数据超过24小时才尝试刷新
        3. 实时数据不存在时才降级到历史数据

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数（兼容基类接口）

        Returns:
            行情数据或错误信息
        """
        # 如果没有提供股票代码，返回提示
        if not stock_code:
            return {
                "error": "缺少股票代码",
                "hint": "请提供要查询的股票代码"
            }

        from ...database import get_db_session
        from ... import models
        from datetime import datetime, timedelta
        import logging

        logger = logging.getLogger(__name__)
        formatted_code = code_format(stock_code)

        # 首先查询实时数据表（兼容两种格式）
        with get_db_session() as session:
            # 尝试查询格式化后的代码（带SH/SZ前缀）
            realtime = session.query(models.StockRealTime).filter(
                models.StockRealTime.stock_code == formatted_code
            ).order_by(models.StockRealTime.update_time.desc()).first()

            # 如果没找到，尝试查询原始代码（不带前缀）
            if not realtime:
                # 提取纯数字代码
                clean_code = stock_code.strip().replace('SH', '').replace('SZ', '')
                realtime = session.query(models.StockRealTime).filter(
                    models.StockRealTime.stock_code == clean_code
                ).order_by(models.StockRealTime.update_time.desc()).first()

            # 检查数据新鲜度并决定使用策略
            if realtime and realtime.update_time:
                time_diff = datetime.now() - realtime.update_time
                data_age_hours = time_diff.total_seconds() / 3600

                # 策略1：如果是今天的数据，直接使用
                if realtime.update_time.date() == datetime.now().date():
                    logger.info(f"使用今天 {time_diff.seconds // 60} 分钟前采集的数据（{realtime.stock_code}）")
                    return self._build_realtime_response(realtime)

                # 策略2：昨天但在24小时内，使用现有数据
                elif data_age_hours < 24:
                    logger.info(f"使用 {data_age_hours:.1f} 小时前的数据（{realtime.stock_code}）")
                    return self._build_realtime_response(realtime)

                # 策略3：数据超过24小时，尝试刷新
                else:
                    logger.info(f"数据过期（{data_age_hours:.1f} 小时），尝试采集最新数据")
                    self._try_refresh_data(formatted_code)
                    # 重新查询
                    realtime = session.query(models.StockRealTime).filter(
                        models.StockRealTime.stock_code == formatted_code
                    ).order_by(models.StockRealTime.update_time.desc()).first()
                    if realtime:
                        return self._build_realtime_response(realtime)

            # 策略4：没有实时数据，尝试采集
            logger.info(f"股票 {formatted_code} 无实时数据，正在采集...")
            success = self._try_refresh_data(formatted_code)
            if success:
                # 重新查询
                realtime = session.query(models.StockRealTime).filter(
                    models.StockRealTime.stock_code == formatted_code
                ).order_by(models.StockRealTime.update_time.desc()).first()
                if realtime:
                    return self._build_realtime_response(realtime)

            # 策略5：所有尝试都失败，降级到历史数据
            logger.warning(f"降级到历史数据查询（{formatted_code}）")
            return self._get_historical_data(session, formatted_code)

    def _try_refresh_data(self, stock_code: str) -> bool:
        """尝试刷新数据（静默失败）"""
        try:
            from ...data.realtime import fetch_job
            fetch_job()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"数据采集失败（非致命）: {e}")
            return False

    def _build_realtime_response(self, realtime) -> Dict[str, Any]:
        """构建实时数据响应"""
        return {
            "stock_code": realtime.stock_code,
            "stock_name": realtime.stock_name or '',
            "latest_price": float(realtime.latest_price) if realtime.latest_price else None,
            "price_change": float(realtime.price_change) if realtime.price_change else None,
            "price_change_rate": float(realtime.price_change_rate) if realtime.price_change_rate else None,
            "volume": int(realtime.volume) if realtime.volume else None,
            "turnover": float(realtime.turnover) if realtime.turnover else None,
            "high_price": float(realtime.high_price) if realtime.high_price else None,
            "low_price": float(realtime.low_price) if realtime.low_price else None,
            "open_price": float(realtime.open_price) if realtime.open_price else None,
            "pre_close_price": float(realtime.pre_close_price) if realtime.pre_close_price else None,
            "update_time": str(realtime.update_time) if realtime.update_time else None,
            "data_source": "realtime"
        }

    def _get_historical_data(self, session, stock_code: str) -> Dict[str, Any]:
        """获取历史日线数据作为回退（兼容两种格式）"""
        from ... import models

        # 尝试查询格式化后的代码
        latest = session.query(models.StockDailyData).filter(
            models.StockDailyData.stock_code == stock_code
        ).order_by(models.StockDailyData.trade_date.desc()).first()

        # 如果没找到，尝试查询纯数字代码
        if not latest:
            clean_code = stock_code.replace('SH', '').replace('SZ', '')
            latest = session.query(models.StockDailyData).filter(
                models.StockDailyData.stock_code == clean_code
            ).order_by(models.StockDailyData.trade_date.desc()).first()

        if not latest:
            return {
                "error": f"未找到股票 {stock_code} 的行情数据",
                "stock_code": stock_code,
                "hint": "实时数据和历史数据均不存在，请检查股票代码是否正确"
            }

        return {
            "stock_code": latest.stock_code,
            "stock_name": getattr(latest, 'stock_name', ''),
            "trade_date": str(latest.trade_date),
            "close_price": float(latest.close) if latest.close else None,
            "open_price": float(latest.open) if latest.open else None,
            "high_price": float(latest.high) if latest.high else None,
            "low_price": float(latest.low) if latest.low else None,
            "volume": int(latest.volume) if latest.volume else None,
            "amount": float(latest.amount) if latest.amount else None,
            "data_source": "historical",
            "note": "使用历史数据，实时数据暂不可用"
        }
