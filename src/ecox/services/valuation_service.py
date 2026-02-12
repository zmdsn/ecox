"""
估值服务层
提供股票和行业估值数据处理的业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import func

from ..repositories import ValuationRepository
from ..database import get_db_session
from .. import models


class ValuationService:
    """估值服务"""

    def __init__(self):
        self.valuation_repo = ValuationRepository()

    def get_stock_valuation(
        self,
        stock_code: str,
        trade_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取股票估值数据"""
        valuation = self.valuation_repo.get_stock_valuation(stock_code, trade_date)

        if valuation:
            return {
                "stock_code": valuation.stock_code,
                "stock_name": valuation.stock_name,
                "trade_date": valuation.trade_date.isoformat() if valuation.trade_date else None,
                "price": float(valuation.price) if valuation.price else None,
                "earnings_per_share": float(valuation.earnings_per_share) if valuation.earnings_per_share else None,
                "book_value_per_share": float(valuation.book_value_per_share) if valuation.book_value_per_share else None,
                "sales_per_share": float(valuation.sales_per_share) if valuation.sales_per_share else None,
                "shares_outstanding": float(valuation.shares_outstanding) if valuation.shares_outstanding else None,
                "total_revenue": float(valuation.total_revenue) if valuation.total_revenue else None,
                "total_assets": float(valuation.total_assets) if valuation.total_assets else None,
                "net_assets": float(valuation.net_assets) if valuation.net_assets else None,
            }
        return None

    def save_valuation(self, valuation_data: Dict) -> Dict[str, Any]:
        """保存估值数据"""
        valuation = self.valuation_repo.save_valuation(valuation_data)

        return {
            "stock_code": valuation.stock_code,
            "trade_date": valuation.trade_date.isoformat() if valuation.trade_date else None,
            "price": float(valuation.price) if valuation.price else None,
        }

    def get_industry_valuation(
        self,
        industry_code: str,
        trade_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取行业估值数据"""
        valuation = self.valuation_repo.get_industry_valuation(industry_code, trade_date)

        if valuation:
            return {
                "industry_code": valuation.industry_code,
                "industry_name": valuation.industry_name,
                "trade_date": valuation.trade_date.isoformat() if valuation.trade_date else None,
                "avg_pe": float(valuation.avg_pe) if valuation.avg_pe else None,
                "avg_pb": float(valuation.avg_pb) if valuation.avg_pb else None,
                "avg_ps": float(valuation.avg_ps) if valuation.avg_ps else None,
                "avg_market_cap": float(valuation.avg_market_cap) if valuation.avg_market_cap else None,
                "sample_count": valuation.sample_count,
            }
        return None

    def calculate_industry_valuation(
        self,
        industry_code: str,
        industry_name: str,
        trade_date: date,
    ) -> Optional[Dict[str, Any]]:
        """计算行业估值指标"""
        with get_db_session() as session:
            # 获取行业内所有股票的估值数据
            query = session.query(
                func.avg(models.StockValuation.price / models.StockValuation.earnings_per_share).label("avg_pe"),
                func.avg(models.StockValuation.price / models.StockValuation.book_value_per_share).label("avg_pb"),
                func.avg(models.StockValuation.price / models.StockValuation.sales_per_share).label("avg_ps"),
                func.sum(models.StockValuation.shares_outstanding * models.StockValuation.price).label("total_market_cap"),
                func.count(models.StockValuation.stock_code).label("sample_count"),
            ).filter(
                models.StockValuation.trade_date == trade_date,
            )

            result = query.first()

            if result and result.sample_count > 0:
                metrics = {
                    "avg_pe": float(result.avg_pe) if result.avg_pe else None,
                    "avg_pb": float(result.avg_pb) if result.avg_pb else None,
                    "avg_ps": float(result.avg_ps) if result.avg_ps else None,
                    "avg_market_cap": float(result.total_market_cap) if result.total_market_cap else None,
                    "sample_count": result.sample_count,
                }

                # 更新或创建行业估值记录
                self.valuation_repo.update_industry_valuation(
                    industry_code, trade_date, metrics
                )

                return {
                    "industry_code": industry_code,
                    "industry_name": industry_name,
                    "trade_date": trade_date.isoformat(),
                    **metrics,
                }

        return None

    def get_cross_industry_comparison(
        self,
        trade_date: date,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """跨行业估值比较"""
        with get_db_session() as session:
            query = session.query(models.IndustryValuation).filter(
                models.IndustryValuation.trade_date == trade_date,
            ).order_by(
                models.IndustryValuation.avg_market_cap.desc(),
            ).limit(limit)

            valuations = query.all()

            return [
                {
                    "industry_code": v.industry_code,
                    "industry_name": v.industry_name,
                    "trade_date": v.trade_date.isoformat() if v.trade_date else None,
                    "avg_pe": float(v.avg_pe) if v.avg_pe else None,
                    "avg_pb": float(v.avg_pb) if v.avg_pb else None,
                    "avg_ps": float(v.avg_ps) if v.avg_ps else None,
                    "avg_market_cap": float(v.avg_market_cap) if v.avg_market_cap else None,
                    "sample_count": v.sample_count,
                }
                for v in valuations
            ]

    def get_historical_valuation(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """获取历史估值数据"""
        with get_db_session() as session:
            query = session.query(models.StockValuation).filter(
                models.StockValuation.stock_code == stock_code,
                models.StockValuation.trade_date >= start_date,
                models.StockValuation.trade_date <= end_date,
            ).order_by(models.StockValuation.trade_date.asc())

            valuations = query.all()

            return [
                {
                    "stock_code": v.stock_code,
                    "trade_date": v.trade_date.isoformat() if v.trade_date else None,
                    "price": float(v.price) if v.price else None,
                    "earnings_per_share": float(v.earnings_per_share) if v.earnings_per_share else None,
                    "book_value_per_share": float(v.book_value_per_share) if v.book_value_per_share else None,
                    "sales_per_share": float(v.sales_per_share) if v.sales_per_share else None,
                }
                for v in valuations
            ]
