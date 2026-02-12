"""
交易策略模块
包含各种技术指标策略和回测分析功能
"""

from .analysis import plot_results, print_analysis
from .indicators import (
    BollingerBandsBreakout,
    DonchianChannelBreakout,
    DoubleMA_Strategy,
    MacdCross,
    RsiMeanReversion,
    SmaCross,
)

__all__ = [
    "DoubleMA_Strategy",
    "MacdCross",
    "DonchianChannelBreakout",
    "BollingerBandsBreakout",
    "RsiMeanReversion",
    "SmaCross",
    "plot_results",
    "print_analysis",
]
