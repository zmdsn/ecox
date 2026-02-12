#!/usr/bin/env python
"""
运行策略回测
使用方法: uv run python scripts/backtest.py [股票代码]
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


import backtrader as bt

from ecox.strategies.indicators import BollingerBandsBreakout


def get_stock_data(symbol="601088"):
    """获取股票数据（简化版，实际使用时需要完善）"""
    # 这里需要实现数据获取逻辑
    # 可以参考 main.py 中的 get_one_stock.py
    print(f"请确保已获取 {symbol} 的数据")
    return None


def run_backtest(symbol="601088"):
    """运行回测"""
    # 1. 获取数据
    # df = get_stock_data(symbol=symbol, start_date="20100101", end_date="20251231")
    # data = bt.feeds.PandasData(dataname=df)

    # 2. 初始化 Cerebro
    cerebro = bt.Cerebro()
    # cerebro.adddata(data)
    cerebro.addstrategy(BollingerBandsBreakout)

    # 3. 设置初始资金和佣金
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.001)

    # 4. 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annualreturn")
    print(f"起始资金: {cerebro.broker.getvalue():.2f}")

    # 5. 运行回测
    # results = cerebro.run()
    # strat = results[0]

    # 6. 输出结果
    # print('最终资金: %.2f' % cerebro.broker.getvalue())
    # print_analysis(strat.analyzers)

    # 7. 绘图
    # plot_results(cerebro)

    print("回测功能需要完善数据获取逻辑")


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "601088"
    run_backtest(symbol)
