"""
数据仓库层
使用 SQLAlchemy ORM 提供数据访问接口
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import func
from sqlalchemy.orm import lazyload, joinedload

from ..database import get_db_session


class StockRepository:
    """股票数据仓库"""

    def __init__(self):
        self.session = None

    def get_by_code(self, stock_code: str) -> Optional[Any]:
        """根据股票代码查询"""
        from .. import models

        with get_db_session() as session:
            return (
                session.query(models.StockBasic)
                .filter(models.StockBasic.stock_code == stock_code)
                .first()
            )

    def get_or_create(self, stock_code: str, stock_name: str) -> Any:
        """获取或创建股票基础信息"""
        from .. import models

        with get_db_session() as session:
            stock = (
                session.query(models.StockBasic)
                .filter(models.StockBasic.stock_code == stock_code)
                .first()
            )

            if not stock:
                stock = models.StockBasic(
                    stock_code=stock_code,
                    stock_name=stock_name,
                )
                session.add(stock)
                session.commit()
                session.refresh(stock)

            return stock

    def update_stock(self, stock_code: str, **kwargs) -> bool:
        """更新股票信息"""
        from .. import models

        with get_db_session() as session:
            count = (
                session.query(models.StockBasic)
                .filter(models.StockBasic.stock_code == stock_code)
                .update(kwargs)
            )
            session.commit()
            return count > 0


class StockDataRepository:
    """股票数据仓库（日线、实时等）"""

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Any]:
        """获取日线数据"""
        from .. import models

        with get_db_session() as session:
            query = session.query(models.StockDailyData).filter(
                models.StockDailyData.stock_code == stock_code
            )

            if start_date:
                query = query.filter(models.StockDailyData.trade_date >= start_date)

            if end_date:
                query = query.filter(models.StockDailyData.trade_date <= end_date)

            query = query.order_by(models.StockDailyData.trade_date.desc())
            return query.limit(limit).all()

    def save_daily_data(self, data_list: List[Dict]) -> Dict[str, int]:
        """批量保存日线数据"""
        from .. import models

        with get_db_session() as session:
            new_count = 0
            for item in data_list:
                # 检查是否已存在
                existing = (
                    session.query(models.StockDailyData)
                    .filter(
                        models.StockDailyData.stock_code == item["stock_code"],
                        models.StockDailyData.trade_date == item["trade_date"],
                        models.StockDailyData.adjust_flag == item.get("adjust_flag", "qfq"),
                    )
                    .first()
                )

                if existing:
                    # 更新现有记录
                    for key, value in item.items():
                        setattr(existing, key, value)
                else:
                    # 创建新记录
                    record = models.StockDailyData(**item)
                    session.add(record)
                    new_count += 1

            session.commit()
            return {"new": new_count, "total": len(data_list)}

    def get_realtime_data(self, stock_codes: Optional[List[str]] = None) -> List[Any]:
        """获取实时数据"""
        from .. import models

        with get_db_session() as session:
            query = session.query(models.StockRealTime).order_by(
                models.StockRealTime.update_time.desc()
            )

            if stock_codes:
                query = query.filter(models.StockRealTime.stock_code.in_(stock_codes))

            return query.all()


class ValuationRepository:
    """估值数据仓库"""

    def get_stock_valuation(
        self,
        stock_code: str,
        trade_date: Optional[date] = None,
    ) -> Optional[Any]:
        """获取股票估值数据"""
        from .. import models

        with get_db_session() as session:
            query = session.query(models.StockValuation).filter(
                models.StockValuation.stock_code == stock_code
            )

            if trade_date:
                query = query.filter(models.StockValuation.trade_date == trade_date)
            else:
                # 获取最新数据
                subquery = (
                    session.query(func.max(models.StockValuation.trade_date))
                    .filter(models.StockValuation.stock_code == stock_code)
                    .scalar_subquery()
                )
                query = query.filter(models.StockValuation.trade_date == subquery)

            return query.first()

    def save_valuation(self, valuation_data: Dict) -> Any:
        """保存估值数据"""
        from .. import models

        with get_db_session() as session:
            # 检查是否已存在
            existing = (
                session.query(models.StockValuation)
                .filter(
                    models.StockValuation.stock_code == valuation_data["stock_code"],
                    models.StockValuation.trade_date == valuation_data["trade_date"],
                )
                .first()
            )

            if existing:
                # 更新现有记录
                for key, value in valuation_data.items():
                    setattr(existing, key, value)
                session.commit()
                return existing
            else:
                # 创建新记录
                valuation = models.StockValuation(**valuation_data)
                session.add(valuation)
                session.commit()
                return valuation

    def get_industry_valuation(
        self,
        industry_code: str,
        trade_date: Optional[date] = None,
    ) -> Optional[Any]:
        """获取行业估值数据"""
        from .. import models

        with get_db_session() as session:
            query = session.query(models.IndustryValuation).filter(
                models.IndustryValuation.industry_code == industry_code
            )

            if trade_date:
                query = query.filter(models.IndustryValuation.trade_date == trade_date)

            return query.first()

    def update_industry_valuation(
        self,
        industry_code: str,
        trade_date: date,
        metrics: Dict,
    ) -> bool:
        """更新行业估值指标"""
        from .. import models

        with get_db_session() as session:
            # 检查是否存在
            existing = (
                session.query(models.IndustryValuation)
                .filter(
                    models.IndustryValuation.industry_code == industry_code,
                    models.IndustryValuation.trade_date == trade_date,
                )
                .first()
            )

            if existing:
                # 更新
                for key, value in metrics.items():
                    setattr(existing, key, value)
                session.commit()
                return True
            else:
                # 创建新记录
                data = {
                    "industry_code": industry_code,
                    "industry_name": industry_code,
                    "trade_date": trade_date,
                    **metrics,
                }
                valuation = models.IndustryValuation(**data)
                session.add(valuation)
                session.commit()
                return True


class FinancialRepository:
    """财务数据仓库（利润表、资产负债表、现金流量表）"""

    def save_profit_sheet(self, sheet_data: Dict) -> Any:
        """保存利润表数据"""
        from .. import models

        with get_db_session() as session:
            profit = models.StockProfitSheet(**sheet_data)
            session.add(profit)
            session.commit()
            return profit

    def save_balance_sheet(self, sheet_data: Dict) -> Any:
        """保存资产负债表数据"""
        from .. import models

        with get_db_session() as session:
            balance = models.StockBalanceSheet(**sheet_data)
            session.add(balance)
            session.commit()
            return balance

    def save_cash_flow_sheet(self, sheet_data: Dict) -> Any:
        """保存现金流量表数据"""
        from .. import models

        with get_db_session() as session:
            cashflow = models.StockCashFlowSheet(**sheet_data)
            session.add(cashflow)
            session.commit()
            return cashflow

    def get_profit_sheet(self, stock_code: str, report_date: str) -> Optional[Any]:
        """获取利润表数据"""
        from .. import models

        with get_db_session() as session:
            return (
                session.query(models.StockProfitSheet)
                .filter(
                    models.StockProfitSheet.stock_code == stock_code,
                    models.StockProfitSheet.report_date == report_date,
                )
                .first()
            )
