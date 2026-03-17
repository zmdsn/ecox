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
        """获取行情数据

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

        formatted_code = code_format(stock_code)

        # 查询最新行情
        with get_db_session() as session:
            # 查询日线数据
            latest = session.query(models.StockDailyData).filter(
                models.StockDailyData.stock_code == formatted_code
            ).order_by(models.StockDailyData.trade_date.desc()).first()

            if not latest:
                return {
                    "error": f"未找到股票 {formatted_code} 的行情数据",
                    "stock_code": formatted_code
                }

            return {
                "stock_code": latest.stock_code,
                "stock_name": getattr(latest, 'stock_name', ''),
                "trade_date": str(latest.trade_date),
                "open_price": float(latest.open_price) if latest.open_price else None,
                "high_price": float(latest.high_price) if latest.high_price else None,
                "low_price": float(latest.low_price) if latest.low_price else None,
                "close_price": float(latest.close_price) if latest.close_price else None,
                "volume": int(latest.volume) if latest.volume else None,
                "amount": float(latest.amount) if latest.amount else None,
                "change_pct": float(latest.change_pct) if hasattr(latest, 'change_pct') and latest.change_pct else None
            }
