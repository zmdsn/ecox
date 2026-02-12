"""
股票服务层
提供股票基础信息和数据管理的业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from ..repositories import StockRepository, StockDataRepository
from ..database import get_db_session


class StockService:
    """股票服务"""

    def __init__(self):
        self.stock_repo = StockRepository()
        self.data_repo = StockDataRepository()

    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基础信息"""
        stock = self.stock_repo.get_by_code(stock_code)
        if stock:
            return {
                "stock_code": stock.stock_code,
                "stock_name": stock.stock_name,
                "industry": stock.industry,
                "list_date": stock.list_date.isoformat() if stock.list_date else None,
                "delist_date": stock.delist_date.isoformat() if stock.delist_date else None,
            }
        return None

    def get_stock_daily_data(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取股票日线数据"""
        data_list = self.data_repo.get_daily_data(stock_code, start_date, end_date, limit)

        return [
            {
                "stock_code": d.stock_code,
                "trade_date": d.trade_date.isoformat() if d.trade_date else None,
                "open": float(d.open) if d.open else None,
                "close": float(d.close) if d.close else None,
                "high": float(d.high) if d.high else None,
                "low": float(d.low) if d.low else None,
                "volume": int(d.volume) if d.volume else None,
                "amount": float(d.amount) if d.amount else None,
                "adjust_flag": d.adjust_flag,
            }
            for d in data_list
        ]

    def get_realtime_data(self, stock_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取实时行情数据"""
        data_list = self.data_repo.get_realtime_data(stock_codes)

        return [
            {
                "stock_code": d.stock_code,
                "stock_name": d.stock_name,
                "latest_price": float(d.latest_price) if d.latest_price else None,
                "price_change": float(d.price_change) if d.price_change else None,
                "price_change_rate": float(d.price_change_rate) if d.price_change_rate else None,
                "volume": int(d.volume) if d.volume else None,
                "turnover": int(d.turnover) if d.turnover else None,
                "high_price": float(d.high_price) if d.high_price else None,
                "low_price": float(d.low_price) if d.low_price else None,
                "open_price": float(d.open_price) if d.open_price else None,
                "pre_close_price": float(d.pre_close_price) if d.pre_close_price else None,
                "update_time": d.update_time.isoformat() if d.update_time else None,
            }
            for d in data_list
        ]

    def save_stock_info(self, stock_code: str, stock_name: str, **kwargs) -> Dict[str, Any]:
        """保存或更新股票基础信息"""
        stock = self.stock_repo.get_or_create(stock_code, stock_name)

        # 更新额外字段
        if kwargs:
            with get_db_session() as session:
                from ..models import StockBasic

                session.query(StockBasic).filter(
                    StockBasic.stock_code == stock_code
                ).update(kwargs)
                session.commit()
                # 重新查询获取最新数据
                updated = session.query(StockBasic).filter(
                    StockBasic.stock_code == stock_code
                ).first()
                if updated:
                    stock.stock_code = updated.stock_code
                    stock.stock_name = updated.stock_name
                    stock.industry = updated.industry
                    stock.list_date = updated.list_date

        return {
            "stock_code": stock.stock_code,
            "stock_name": stock.stock_name,
            "industry": stock.industry,
            "list_date": stock.list_date.isoformat() if stock.list_date else None,
        }

    def save_daily_data(self, data_list: List[Dict]) -> int:
        """批量保存日线数据"""
        return self.data_repo.save_daily_data(data_list)

    def get_stock_list(self, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取股票列表"""
        from ..models import StockBasic

        with get_db_session() as session:
            query = session.query(StockBasic)

            if industry:
                query = query.filter(StockBasic.industry == industry)

            stocks = query.all()

            return [
                {
                    "stock_code": s.stock_code,
                    "stock_name": s.stock_name,
                    "industry": s.industry,
                    "list_date": s.list_date.isoformat() if s.list_date else None,
                }
                for s in stocks
            ]

    def delete_stock(self, stock_code: str) -> bool:
        """删除股票数据"""
        from ..models import StockBasic

        with get_db_session() as session:
            count = session.query(StockBasic).filter(
                StockBasic.stock_code == stock_code
            ).delete()
            session.commit()
            return count > 0
