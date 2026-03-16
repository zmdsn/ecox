"""
数据采集模块
包含实时行情、历史日线、股票信息、财务报表等数据采集功能
"""

from .realtime import (
    get_a_share_real_time_data,
    is_a_stock_trading_time,
    run_job,
    initialize_database as init_realtime_database,
)
from .daily import (
    main_daily_update,
    initial_full_load,
    initialize_database as init_daily_database,
)
from .shares import sync_a_share_basic, validate_a_share_basic
from .report import crawl_profit_sheet, crawl_balance_sheet, crawl_cash_flow_sheet

__all__ = [
    # 实时行情
    "get_a_share_real_time_data",
    "is_a_stock_trading_time",
    "run_job",
    "init_realtime_database",
    # 日线数据
    "main_daily_update",
    "initial_full_load",
    "init_daily_database",
    # 股票信息
    "sync_a_share_basic",
    "validate_a_share_basic",
    # 财务报表
    "crawl_profit_sheet",
    "crawl_balance_sheet",
    "crawl_cash_flow_sheet",
]
