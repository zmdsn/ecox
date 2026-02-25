"""
Ecox - A股数据采集和量化回测系统
"""

# 配置和基础模块
from .config import config, PG_CONFIG
from .db import get_connection, get_connection_with_retry, get_pg_conn, get_pg_connection
from .utils import code_format, parse_stock_code, is_sh_stock, is_sz_stock, is_bj_stock

# 数据采集模块
from .data import (
    init_realtime_database,
    init_daily_database,
    crawl_balance_sheet,
    crawl_cash_flow_sheet,
    crawl_profit_sheet,
    get_a_share_real_time_data,
    initial_full_load,
    is_a_stock_trading_time,
    main_daily_update,
    run_job,
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
    fetch_and_save_valuation,
    fetch_stock_valuation,
    calculate_industry_valuation,
    get_cross_industry_comparison,
    get_stock_valuation_history,
    initialize_database as init_valuation_database,
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
from .mcp_server import mcp, get_dupont_analysis, get_sql_data

# ORM 和服务层
from .database import init_db, get_db_session, DatabaseSession
from .repositories import (
    StockRepository,
    StockDataRepository,
    ValuationRepository,
    FinancialRepository,
)
from .services import (
    StockService,
    ValuationService,
    DataCollectionService,
    PriceService,
)
from .models import StockPrice

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
    "init_realtime_database",
    "init_daily_database",
    "crawl_balance_sheet",
    "crawl_cash_flow_sheet",
    "crawl_profit_sheet",
    "get_a_share_real_time_data",
    "initial_full_load",
    "is_a_stock_trading_time",
    "main_daily_update",
    "run_job",
    "sync_a_share_basic",
    "validate_a_share_basic",
    # 估值
    "calculate_pe",
    "calculate_pb",
    "calculate_ps",
    "calculate_market_value",
    "calculate_valuation_metrics",
    "fetch_and_save_valuation",
    "fetch_stock_valuation",
    "calculate_industry_valuation",
    "get_cross_industry_comparison",
    "get_stock_valuation_history",
    "init_valuation_database",
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
    # ORM 和服务层
    "init_db",
    "get_db_session",
    "DatabaseSession",
    "StockRepository",
    "StockDataRepository",
    "ValuationRepository",
    "FinancialRepository",
    "StockService",
    "ValuationService",
    "DataCollectionService",
    "PriceService",
    "StockPrice",
]
