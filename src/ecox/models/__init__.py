"""
数据库模型
使用 SQLAlchemy ORM 定义所有数据表
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    Date,
    DateTime,
    BigInteger,
    Text,
    Index,
    UniqueConstraint,
    ForeignKey,
    JSON,
)

# 从 database 模块导入共享的 Base
from ..database import Base

# 导入 BaseMixin
from .base import BaseMixin


class StockRealTime(Base):
    """实时行情表"""

    __tablename__ = "a_share_real_time"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    latest_price = Column(Numeric(10, 2))
    price_change = Column(Numeric(10, 2))
    price_change_rate = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    turnover = Column(BigInteger)
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    open_price = Column(Numeric(10, 2))
    pre_close_price = Column(Numeric(10, 2))
    update_time = Column(DateTime, nullable=False, index=True)

    def __repr__(self):
        return f"<StockRealTime({self.stock_code} {self.update_time})>"


class StockBasic(Base):
    """股票基础信息表"""

    __tablename__ = "a_share_basic"

    stock_code = Column(String(20), primary_key=True)
    stock_name = Column(String(100), nullable=False)
    industry = Column(String(50))
    list_date = Column(Date)
    delist_date = Column(Date)
    update_time = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StockBasic({self.stock_code} {self.stock_name})>"


class StockDailyData(Base):
    """日线数据表"""

    __tablename__ = "stock_daily_data"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    amount = Column(Numeric(20, 2))
    adjust_flag = Column(String(10), default="qfq")
    update_time = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", "adjust_flag"),
        Index("idx_stock_date", "stock_code", "trade_date"),
    )

    def __repr__(self):
        return f"<StockDailyData({self.stock_code} {self.trade_date})>"


class StockValuation(Base):
    """股票估值数据表"""

    __tablename__ = "stock_valuation"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    trade_date = Column(Date, nullable=False, index=True)
    price = Column(Numeric(10, 2))
    earnings_per_share = Column(Numeric(10, 4))
    book_value_per_share = Column(Numeric(10, 4))
    sales_per_share = Column(Numeric(10, 4))
    shares_outstanding = Column(Numeric(18, 2))
    total_revenue = Column(Numeric(20, 2))
    total_assets = Column(Numeric(20, 2))
    net_assets = Column(Numeric(20, 2))
    update_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date"),
        Index("idx_valuation_date", "stock_code", "trade_date"),
    )

    def __repr__(self):
        return f"<StockValuation({self.stock_code} {self.trade_date})>"


class IndustryValuation(Base):
    """行业估值数据表"""

    __tablename__ = "industry_valuation"

    id = Column(Integer, primary_key=True)
    industry_code = Column(String(20), primary_key=True)
    industry_name = Column(String(100))
    trade_date = Column(Date, nullable=False, index=True)
    avg_pe = Column(Numeric(10, 2))
    avg_pb = Column(Numeric(10, 2))
    avg_ps = Column(Numeric(10, 2))
    avg_market_cap = Column(Numeric(20, 2))
    sample_count = Column(Integer)
    update_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("industry_code", "trade_date"),
        Index("idx_industry_date", "industry_code", "trade_date"),
    )

    def __repr__(self):
        return f"<IndustryValuation({self.industry_code} {self.trade_date})>"


class StockProfitSheet(Base):
    """利润表"""

    __tablename__ = "stock_profit_sheet"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20))
    report_type = Column(String(10))
    total_revenue = Column(Numeric(20, 2))
    operating_profit = Column(Numeric(20, 2))
    net_profit = Column(Numeric(20, 2))
    basic_eps = Column(Numeric(10, 4))
    diluted_eps = Column(Numeric(10, 4))
    extra_data = Column(JSON)  # 存储完整财报数据
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_profit_report"),
    )

    def __repr__(self):
        return f"<StockProfitSheet({self.stock_code} {self.report_date})>"


class StockBalanceSheet(Base):
    """资产负债表"""

    __tablename__ = "stock_balance_sheet"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20))
    report_type = Column(String(10))
    total_assets = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    owner_equity = Column(Numeric(20, 2))
    fixed_assets = Column(Numeric(20, 2))
    extra_data = Column(JSON)  # 存储完整财报数据
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_balance_report"),
    )

    def __repr__(self):
        return f"<StockBalanceSheet({self.stock_code} {self.report_date})>"


class StockCashFlowSheet(Base):
    """现金流量表"""

    __tablename__ = "stock_cash_flow_sheet"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(String(20))
    report_type = Column(String(10))
    operating_cash_flow = Column(Numeric(20, 2))
    investing_cash_flow = Column(Numeric(20, 2))
    financing_cash_flow = Column(Numeric(20, 2))
    net_cash_flow = Column(Numeric(20, 2))
    extra_data = Column(JSON)  # 存储完整财报数据
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_cashflow_report"),
    )

    def __repr__(self):
        return f"<StockCashFlowSheet({self.stock_code} {self.report_date})>"


class UpdateLog(Base):
    """更新日志表"""

    __tablename__ = "update_log"

    id = Column(Integer, primary_key=True)
    run_time = Column(DateTime, nullable=False)
    success_count = Column(Integer)
    failed_count = Column(Integer)
    new_rows_count = Column(Integer)
    error_message = Column(Text)


class StockPrice(Base):
    """股票每日价格表（简化版，用于快速查询）"""
    
    __tablename__ = "stock_price"
    
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    close_price = Column(Numeric(10, 2), nullable=False)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    amount = Column(Numeric(20, 2))
    change_rate = Column(Numeric(10, 4))  # 涨跌幅
    update_time = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date"),
        Index("idx_price_date", "stock_code", "trade_date"),
    )
    
    def __repr__(self):
        return f"<StockPrice({self.stock_code} {self.trade_date} {self.close_price})>"


class DataAlert(Base):
    """数据告警记录表"""

    __tablename__ = "data_alerts"

    id = Column(Integer, primary_key=True)
    alert_level = Column(String(10), nullable=False, index=True)  # ERROR/WARNING/INFO
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    alert_type = Column(String(50), nullable=False, index=True)  # price_invalid/volume_zero/...
    alert_message = Column(Text, nullable=False)
    raw_data = Column(JSON)  # 原始数据
    trade_date = Column(Date, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)

    def __repr__(self):
        return f"<DataAlert({self.alert_level} {self.stock_code} {self.alert_type})>"


class StockFinancialMetrics(Base):
    """统一财务指标表"""
    __tablename__ = "stock_financial_metrics"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    report_date = Column(String(20), nullable=False, index=True)
    report_type = Column(String(10))

    # === 盈利能力 ===
    roe = Column(Numeric(10, 4))
    roa = Column(Numeric(10, 4))
    roic = Column(Numeric(10, 4))
    gross_margin = Column(Numeric(10, 4))
    net_margin = Column(Numeric(10, 4))
    operating_margin = Column(Numeric(10, 4))

    # === 现金流分析 ===
    fcff = Column(Numeric(20, 4))
    fcfe = Column(Numeric(20, 4))
    capex = Column(Numeric(20, 4))
    cash_conversion_rate = Column(Numeric(10, 4))
    ocf_to_sales = Column(Numeric(10, 4))

    # === 偿债能力 ===
    debt_ratio = Column(Numeric(10, 4))
    current_ratio = Column(Numeric(10, 4))
    quick_ratio = Column(Numeric(10, 4))
    interest_coverage = Column(Numeric(10, 4))

    # === 营运能力 ===
    inventory_turnover = Column(Numeric(10, 4))
    receivables_turnover = Column(Numeric(10, 4))
    asset_turnover = Column(Numeric(10, 4))

    # === 成长能力 ===
    revenue_growth_1y = Column(Numeric(10, 4))
    profit_growth_1y = Column(Numeric(10, 4))
    revenue_cagr_5y = Column(Numeric(10, 4))
    profit_cagr_5y = Column(Numeric(10, 4))
    fcff_cagr_5y = Column(Numeric(10, 4))

    # === 估值指标 ===
    pe_ratio = Column(Numeric(10, 4))
    pb_ratio = Column(Numeric(10, 4))
    ps_ratio = Column(Numeric(10, 4))
    ev_ebitda = Column(Numeric(10, 4))
    peg_ratio = Column(Numeric(10, 4))

    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "report_date", name="uix_financial_metrics"),
    )

    def __repr__(self):
        return f"<StockFinancialMetrics({self.stock_code} {self.report_date})>"


# 导出所有模型
__all__ = [
    "Base",
    "BaseMixin",
    "StockRealTime",
    "StockBasic",
    "StockDailyData",
    "StockValuation",
    "IndustryValuation",
    "StockProfitSheet",
    "StockBalanceSheet",
    "StockCashFlowSheet",
    "UpdateLog",
    "StockPrice",
    "DataAlert",
    "StockFinancialMetrics",
]
