"""
Ecox - A股数据采集和量化回测系统
"""

# 配置和基础模块
from .config import config, PG_CONFIG
from .db import get_connection, get_connection_with_retry, get_pg_conn, get_pg_connection
from .utils import code_format, parse_stock_code, is_sh_stock, is_sz_stock, is_bj_stock

# 数据采集模块
from .data import (
    StockDB,
    crawl_balance_sheet,
    crawl_cash_flow_sheet,
    crawl_profit_sheet,
    get_a_share_real_time_data,
    initial_full_load,
    is_a_stock_trading_time,
    main_daily_update,
    sync_a_share_basic,
    validate_a_share_basic,
)

# 估值模块
from .valuation import (
    calculate_pe,
    calculate_pb,
    calculate_ps,
    calculate_market_value,
    calculate_valuation_metrics,
    fetch_valuation_data,
    fetch_stock_valuation,
    save_valuation_to_db,
)

# 交易策略模块
from .strategies import (
    BollingerBandsBreakout,
    DonchianChannelBreakout,
    DoubleMA_Strategy,
    MacdCross,
    RsiMeanReversion,
    SmaCross,
    plot_results,
    print_analysis,
)

# MCP 服务器模块
from .mcp import mcp, get_dupont_analysis, get_sql_data

__all__ = [
    # 配置
    "config",
    "PG_CONFIG",
    # 数据库
    "get_connection",
    "get_connection_with_retry",
    "get_pg_conn",
    "get_pg_connection",
    # 工具函数
    "code_format",
    "parse_stock_code",
    "is_sh_stock",
    "is_sz_stock",
    "is_bj_stock",
    # 数据采集
    "StockDB",
    "crawl_balance_sheet",
    "crawl_cash_flow_sheet",
    "crawl_profit_sheet",
    "get_a_share_real_time_data",
    "initial_full_load",
    "is_a_stock_trading_time",
    "main_daily_update",
    "sync_a_share_basic",
    "validate_a_share_basic",
    # 估值
    "calculate_pe",
    "calculate_pb",
    "calculate_ps",
    "calculate_market_value",
    "calculate_valuation_metrics",
    "fetch_valuation_data",
    "fetch_stock_valuation",
    "save_valuation_to_db",
    # 交易策略
    "DoubleMA_Strategy",
    "MacdCross",
    "DonchianChannelBreakout",
    "BollingerBandsBreakout",
    "RsiMeanReversion",
    "SmaCross",
    "plot_results",
    "print_analysis",
    # MCP
    "mcp",
    "get_dupont_analysis",
    "get_sql_data",
]
