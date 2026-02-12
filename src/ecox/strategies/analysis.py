"""
回测分析模块
提供回测结果分析和可视化功能
"""

import matplotlib.pyplot as plt


def plot_results(cerebro):
    """绘制回测结果图表"""
    cerebro.plot(style="candlestick")
    plt.show()


def print_analysis(analyzer):
    """打印分析器结果"""
    print("\n--- 夏普比率 ---")
    print(analyzer.sharpe.get_analysis())
    print("\n--- 最大回撤 ---")
    print(analyzer.drawdown.get_analysis())
    print("\n--- 年化收益率 ---")
    print(analyzer.annualreturn.get_analysis())
