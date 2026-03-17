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
        """获取行情数据（智能自动更新）

        如果实时数据过期（超过15分钟），会自动触发数据采集

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

        # 首先查询实时数据表
        with get_db_session() as session:
            realtime = session.query(models.StockRealTime).filter(
                models.StockRealTime.stock_code == formatted_code
            ).order_by(models.StockRealTime.update_time.desc()).first()

            # 检查数据是否过期（15分钟）
            need_refresh = True
            if realtime and realtime.update_time:
                time_diff = datetime.now() - realtime.update_time
                if time_diff < timedelta(minutes=15):
                    need_refresh = False
                    logger.debug(f"数据新鲜度良好，更新于 {time_diff.seconds // 60} 分钟前")

            # 如果数据过期或不存在，自动触发采集
            if need_refresh:
                logger.info(f"股票 {formatted_code} 数据已过期或不存在，正在自动采集最新数据...")
                try:
                    from ...data.realtime import fetch_job
                    fetch_job()
                    logger.info(f"数据采集完成，重新查询 {formatted_code}")

                    # 重新查询
                    realtime = session.query(models.StockRealTime).filter(
                        models.StockRealTime.stock_code == formatted_code
                    ).order_by(models.StockRealTime.update_time.desc()).first()
                except Exception as e:
                    logger.error(f"自动采集失败: {e}")
                    # 如果采集失败，尝试使用历史数据
                    return self._get_historical_data(session, formatted_code)

            # 返回实时数据
            if realtime:
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
            else:
                # 如果还是没有实时数据，回退到历史数据
                return self._get_historical_data(session, formatted_code)

    def _get_historical_data(self, session, stock_code: str) -> Dict[str, Any]:
        """获取历史日线数据作为回退"""
        from ... import models

        latest = session.query(models.StockDailyData).filter(
            models.StockDailyData.stock_code == stock_code
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
            "close_price": float(latest.close_price) if latest.close_price else None,
            "open_price": float(latest.open_price) if latest.open_price else None,
            "high_price": float(latest.high_price) if latest.high_price else None,
            "low_price": float(latest.low_price) if latest.low_price else None,
            "volume": int(latest.volume) if latest.volume else None,
            "amount": float(latest.amount) if latest.amount else None,
            "change_pct": float(latest.change_pct) if hasattr(latest, 'change_pct') and latest.change_pct else None,
            "data_source": "historical",
            "note": "使用历史数据，实时数据暂不可用"
        }
