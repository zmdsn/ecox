"""
股票价格服务层
提供每日价格查询和更新的业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import func

from ..database import get_db_session
from ..repositories import StockDataRepository
from .. import models


class PriceService:
    """股票价格服务"""
    
    def __init__(self):
        self.data_repo = StockDataRepository()
    
    def get_latest_price(
        self, 
        stock_code: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取最新价格数据"""
        from ..models import StockPrice
        
        with get_db_session() as session:
            query = session.query(
                StockPrice.stock_code,
                StockPrice.trade_date,
                StockPrice.close_price,
                StockPrice.open_price,
                StockPrice.high_price,
                StockPrice.low_price,
                StockPrice.volume,
                StockPrice.change_rate,
            ).filter(
                StockPrice.stock_code == stock_code
            ).order_by(
                StockPrice.trade_date.desc()
            ).limit(days)
            
            prices = query.all()
            
            return [
                {
                    "stock_code": p.stock_code,
                    "trade_date": p.trade_date.isoformat() if p.trade_date else None,
                    "close": float(p.close_price) if p.close_price else None,
                    "open": float(p.open_price) if p.open_price else None,
                    "high": float(p.high_price) if p.high_price else None,
                    "low": float(p.low_price) if p.low_price else None,
                    "volume": int(p.volume) if p.volume else None,
                    "change_rate": float(p.change_rate) if p.change_rate else None,
                }
                for p in prices
            ]
    
    def get_price_range(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """获取指定日期范围的价格数据"""
        from ..models import StockPrice
        
        with get_db_session() as session:
            prices = session.query(StockPrice).filter(
                StockPrice.stock_code == stock_code,
                StockPrice.trade_date >= start_date,
                StockPrice.trade_date <= end_date,
            ).order_by(
                StockPrice.trade_date.asc()
            ).all()
            
            return [
                {
                    "stock_code": p.stock_code,
                    "trade_date": p.trade_date.isoformat() if p.trade_date else None,
                    "close": float(p.close_price) if p.close_price else None,
                    "open": float(p.open_price) if p.open_price else None,
                    "high": float(p.high_price) if p.high_price else None,
                    "low": float(p.low_price) if p.low_price else None,
                    "volume": int(p.volume) if p.volume else None,
                }
                for p in prices
            ]
    
    def save_price_data(
        self, 
        data_list: List[Dict]
    ) -> Dict[str, int]:
        """批量保存价格数据"""
        from ..models import StockPrice
        
        with get_db_session() as session:
            saved_count = 0
            updated_count = 0
            
            for item in data_list:
                # 检查是否已存在
                existing = session.query(StockPrice).filter(
                    StockPrice.stock_code == item["stock_code"],
                    StockPrice.trade_date == item["trade_date"],
                ).first()
                
                if existing:
                    # 更新
                    for key, value in item.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated_count += 1
                else:
                    # 新增
                    price = StockPrice(**item)
                    session.add(price)
                    saved_count += 1
            
            session.commit()
            
            return {
                "saved": saved_count,
                "updated": updated_count,
                "total": len(data_list),
            }
    
    def calculate_change_rate(
        self,
        stock_code: str,
        trade_date: date,
    ) -> Optional[float]:
        """计算涨跌幅"""
        from ..models import StockPrice
        
        with get_db_session() as session:
            # 获取前一日数据
            prev_price = session.query(StockPrice.close_price).filter(
                StockPrice.stock_code == stock_code,
                StockPrice.trade_date < trade_date,
            ).order_by(
                StockPrice.trade_date.desc()
            ).first()
            
            # 获取当日数据
            curr_price = session.query(StockPrice.close_price).filter(
                StockPrice.stock_code == stock_code,
                StockPrice.trade_date == trade_date,
            ).first()
            
            if prev_price and curr_price:
                prev = float(prev_price[0])
                curr = float(curr_price)
                return ((curr - prev) / prev) * 100 if prev > 0 else 0
            
            return None
