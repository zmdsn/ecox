"""
估值数据采集模块
从 akshare 获取估值数据，并使用 ORM 存入数据库
"""
import time
import pandas as pd
import akshare as ak
from typing import Optional, Dict, List
from datetime import date, datetime
import logging

# 导入服务和数据库模块
from ..services import ValuationService, DataCollectionService
from ..database import get_db_session
from .. import models

# 数据采集间隔
CALL_INTERVAL = 0.5  # 秒

# 日志配置
logger = logging.getLogger(__name__)


def initialize_database():
    """初始化数据库表结构"""
    from ..database import init_db

    try:
        db = init_db()
        db.create_all()
        logger.info("估值数据表结构初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def fetch_stock_valuation(
    stock_code: str,
    stock_name: str,
    trade_date: Optional[date] = None,
) -> Optional[Dict]:
    """
    获取单只股票的估值数据

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        trade_date: 交易日期

    Returns:
        估值数据字典
    """
    try:
        df = ak.stock_zh_a_spot_em()

        # 查找对应股票的数据
        stock_df = df[df["代码"] == stock_code]

        if stock_df.empty:
            logger.warning(f"未找到 {stock_code} 的数据")
            return None

        row = stock_df.iloc[0]

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "trade_date": trade_date or datetime.now().date(),
            "price": float(row.get("最新价", 0)) if pd.notna(row.get("最新价")) else None,
            "earnings_per_share": None,  # 需要其他数据源
            "book_value_per_share": None,  # 需要其他数据源
            "sales_per_share": None,  # 需要其他数据源
            "shares_outstanding": None,  # 需要其他数据源
            "total_revenue": None,
            "total_assets": None,
            "net_assets": None,
        }

    except Exception as e:
        logger.error(f"获取 {stock_code} 估值数据失败: {e}")
        return None


def save_valuation_data(
    data_list: List[Dict],
    service: ValuationService,
) -> Dict[str, int]:
    """
    批量保存估值数据

    Args:
        data_list: 估值数据列表
        service: 估值服务实例

    Returns:
        统计信息
    """
    success_count = 0
    failed_count = 0

    for data in data_list:
        try:
            service.save_valuation(data)
            success_count += 1
        except Exception as e:
            logger.error(f"保存 {data.get('stock_code')} 估值数据失败: {e}")
            failed_count += 1

    return {"success": success_count, "failed": failed_count}


def fetch_and_save_valuation(
    stock_codes: Optional[List[str]] = None,
    trade_date: Optional[date] = None,
) -> Dict[str, int]:
    """
    批量获取并保存估值数据

    Args:
        stock_codes: 股票代码列表，None 表示全市场
        trade_date: 交易日期

    Returns:
        统计信息 {"success": int, "failed": int}
    """
    service = ValuationService()
    trade_date = trade_date or datetime.now().date()

    # 获取股票列表
    if stock_codes is None:
        from ..services import StockService
        stock_service = StockService()
        stock_list = stock_service.get_stock_list()
        stock_codes = [s["stock_code"] for s in stock_list]

        # 限制数量避免请求过多
        if len(stock_codes) > 100:
            stock_codes = stock_codes[:100]
            logger.warning(f"股票数量过多，仅处理前 {len(stock_codes)} 只")

    all_data = []

    for code in stock_codes:
        # 先获取股票名称
        from ..services import StockService
        stock_service = StockService()
        stock_info = stock_service.get_stock_info(code)

        if not stock_info:
            logger.warning(f"未找到 {code} 的基础信息，跳过")
            continue

        valuation_data = fetch_stock_valuation(
            code, stock_info["stock_name"], trade_date
        )

        if valuation_data:
            all_data.append(valuation_data)

        time.sleep(CALL_INTERVAL)

    # 批量保存
    result = save_valuation_data(all_data, service)

    logger.info(f"估值数据采集完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")

    return result


def calculate_industry_valuation(
    trade_date: Optional[date] = None,
) -> List[Dict]:
    """
    计算行业估值指标
    从 stock_valuation 表计算各行业的平均估值指标

    Args:
        trade_date: 交易日期

    Returns:
        行业估值列表
    """
    service = ValuationService()
    trade_date = trade_date or datetime.now().date()

    # 获取所有行业
    from ..services import StockService
    stock_service = StockService()

    industries = {}
    stock_list = stock_service.get_stock_list()

    # 按行业分组股票
    for stock in stock_list:
        industry = stock.get("industry")
        if industry and industry not in industries:
            industries[industry] = []

    # 计算各行业估值
    industry_valuations = []

    for industry_code in industries.keys():
        try:
            valuation = service.calculate_industry_valuation(
                industry_code=industry_code,
                industry_name=industry_code,
                trade_date=trade_date,
            )

            if valuation:
                industry_valuations.append(valuation)

        except Exception as e:
            logger.error(f"计算 {industry_code} 行业估值失败: {e}")

    logger.info(f"计算了 {len(industry_valuations)} 个行业的估值指标")

    return industry_valuations


def get_cross_industry_comparison(
    trade_date: Optional[date] = None,
    limit: int = 20,
) -> List[Dict]:
    """
    获取跨行业估值比较

    Args:
        trade_date: 交易日期
        limit: 返回数量限制

    Returns:
        行业估值比较列表
    """
    service = ValuationService()
    trade_date = trade_date or datetime.now().date()

    return service.get_cross_industry_comparison(trade_date, limit)


def get_stock_valuation_history(
    stock_code: str,
    start_date: date,
    end_date: date,
) -> List[Dict]:
    """
    获取股票历史估值数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        历史估值数据列表
    """
    service = ValuationService()
    return service.get_historical_valuation(stock_code, start_date, end_date)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    # 初始化数据库
    initialize_database()

    # 测试数据采集
    logger.info("开始测试估值数据采集...")

    result = fetch_and_save_valuation(
        stock_codes=["600000", "000001"],
        trade_date=datetime.now().date(),
    )

    logger.info(f"测试完成: {result}")

    # 计算行业估值
    # industry_valuations = calculate_industry_valuation()
    # logger.info(f"行业估值: {industry_valuations}")
