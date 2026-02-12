"""
估值指标计算模块
提供 PE、PB、PS、市销率、市净率等常用估值指标计算
"""

import pandas as pd
import numpy as np
from typing import Optional, Union


def calculate_pe(
    price: float, earnings_per_share: float, shares_outstanding: Optional[float] = None
) -> float:
    """
    计算市盈率（PE Ratio）

    Args:
        price: 股价
        earnings_per_share: 每股收益
        shares_outstanding: 总股本（可选，用于计算总市值）

    Returns:
        市盈率
    """
    if earnings_per_share == 0:
        return 0.0
    return price / earnings_per_share


def calculate_pb(price: float, book_value_per_share: float) -> float:
    """
    计算市净率（PB Ratio）

    Args:
        price: 股价
        book_value_per_share: 每股净资产

    Returns:
        市净率
    """
    if book_value_per_share == 0:
        return 0.0
    return price / book_value_per_share


def calculate_ps(price: float, sales_per_share: float) -> float:
    """
    计算市销率（PS Ratio）

    Args:
        price: 股价
        sales_per_share: 每股销售额

    Returns:
        市销率
    """
    if sales_per_share == 0:
        return 0.0
    return price / sales_per_share


def calculate_market_value(price: float, shares_outstanding: float) -> float:
    """
    计算总市值

    Args:
        price: 股价
        shares_outstanding: 总股本

    Returns:
        总市值（元）
    """
    return price * shares_outstanding


def calculate_valuation_metrics(
    price: float,
    earnings_per_share: float,
    book_value_per_share: float,
    sales_per_share: float,
    shares_outstanding: Optional[float] = None,
    total_revenue: Optional[float] = None,
    total_assets: Optional[float] = None,
    net_assets: Optional[float] = None,
) -> dict:
    """
    计算综合估值指标

    Args:
        price: 股价
        earnings_per_share: 每股收益
        book_value_per_share: 每股净资产
        sales_per_share: 每股销售额
        shares_outstanding: 总股本（可选）
        total_revenue: 营业总收入（可选，用于市销率调整）
        total_assets: 总资产（可选，用于市净率调整）
        net_assets: 净资产（可选）

    Returns:
        包含各项估值指标的字典
    """
    result = {
        "price": price,
        "pe": calculate_pe(price, earnings_per_share),
        "pb": calculate_pb(price, book_value_per_share),
        "ps": calculate_ps(price, sales_per_share),
        "market_cap": (
            calculate_market_value(price, shares_outstanding) if shares_outstanding else None
        ),
    }

    # 可选：调整后指标
    if total_revenue and shares_outstanding:
        result["ps_adjusted"] = (price * shares_outstanding) / total_revenue

    if total_assets and shares_outstanding:
        result["pb_adjusted"] = (price * shares_outstanding) / total_assets

    if net_assets and shares_outstanding:
        result["price_to_book"] = price / (net_assets / shares_outstanding)

    return result


def calculate_industry_average(metrics_list: list[dict], metric: str = "pe") -> float:
    """
    计算行业平均估值指标

    Args:
        metrics_list: 包含多只股票估值指标的列表
        metric: 要计算平均的指标名称（pe/pb/ps）

    Returns:
        行业平均值
    """
    if not metrics_list:
        return 0.0

    values = [
        m.get(metric, 0)
        for m in metrics_list
        if m.get(metric, 0) is not None and m.get(metric, 0) > 0
    ]
    if not values:
        return 0.0

    return np.mean(values)


def calculate_relative_valuation(
    stock_metrics: dict,
    industry_avg_pe: float,
    industry_avg_pb: float,
) -> dict:
    """
    计算相对估值（与行业平均对比）

    Args:
        stock_metrics: 股票估值指标
        industry_avg_pe: 行业平均 PE
        industry_avg_pb: 行业平均 PB

    Returns:
        相对估值结果
    """
    stock_pe = stock_metrics.get("pe", 0)
    stock_pb = stock_metrics.get("pb", 0)

    result = {
        "stock_pe": stock_pe,
        "stock_pb": stock_pb,
        "industry_avg_pe": industry_avg_pe,
        "industry_avg_pb": industry_avg_pb,
        "pe_relative": stock_pe / industry_avg_pe if industry_avg_pe > 0 else None,
        "pb_relative": stock_pb / industry_avg_pb if industry_avg_pb > 0 else None,
    }

    # 估值判断
    if result["pe_relative"] and result["pb_relative"]:
        # 同时低于行业中位数，被低估
        if result["pe_relative"] < 1 and result["pb_relative"] < 1:
            result["valuation_status"] = "低估"
        # 同时高于行业中位数，被高估
        elif result["pe_relative"] > 1 and result["pb_relative"] > 1:
            result["valuation_status"] = "高估"
        else:
            result["valuation_status"] = "正常"
    else:
        result["valuation_status"] = "数据不足"

    return result


def filter_by_valuation(
    df: pd.DataFrame,
    max_pe: float = 30.0,
    max_pb: float = 3.0,
    min_market_cap: Optional[float] = None,
) -> pd.DataFrame:
    """
    根据估值指标筛选股票

    Args:
        df: 包含估值数据的 DataFrame
        max_pe: 最大 PE 值
        max_pb: 最大 PB 值
        min_market_cap: 最小市值（可选）

    Returns:
        筛选后的 DataFrame
    """
    mask = pd.Series([True] * len(df))

    if "pe" in df.columns:
        mask &= (df["pe"] > 0) & (df["pe"] <= max_pe)

    if "pb" in df.columns:
        mask &= (df["pb"] > 0) & (df["pb"] <= max_pb)

    if min_market_cap is not None and "market_cap" in df.columns:
        mask &= df["market_cap"] >= min_market_cap

    return df[mask]
