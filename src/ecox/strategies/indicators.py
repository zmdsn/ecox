"""
交易策略模块
包含各种技术指标策略类
"""

import backtrader as bt


class DoubleMA_Strategy(bt.Strategy):
    """双均线交叉策略"""

    params = (
        ("ma_short", 5),
        ("ma_long", 20),
        ("printlog", True),
    )

    def __init__(self):
        self.ma_short = bt.ind.SMA(self.data.close, period=self.params.ma_short)
        self.ma_long = bt.ind.SMA(self.data.close, period=self.params.ma_long)
        self.crossover = bt.ind.CrossOver(self.ma_short, self.ma_long)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.sell()

    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()}, {txt}")


class MacdCross(bt.Strategy):
    """MACD 交叉策略"""

    params = (
        ("macd1", 12),
        ("macd2", 26),
        ("macdsig", 9),
    )

    def __init__(self):
        self.macd = bt.ind.MACD(
            self.data.close,
            period_me1=self.p.macd1,
            period_me2=self.p.macd2,
            period_signal=self.p.macdsig,
        )
        self.crossover = bt.ind.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.sell()


class DonchianChannelBreakout(bt.Strategy):
    """唐奇安通道突破策略"""

    params = (("channel_period", 20),)

    def __init__(self):
        self.dchannel = bt.ind.DonchianChannels(
            self.data.high, self.data.low, period=self.p.channel_period
        )

    def next(self):
        if not self.position and self.data.close > self.dchannel.lines.dchigh:
            self.buy()
        elif self.position and self.data.close < self.dchannel.lines.dclow:
            self.sell()


class BollingerBandsBreakout(bt.Strategy):
    """布林带突破策略"""

    params = (
        ("bb_period", 20),
        ("bb_dev", 2),
    )

    def __init__(self):
        self.bb = bt.ind.BollingerBands(
            self.data.close, period=self.p.bb_period, devfactor=self.p.bb_dev
        )

    def next(self):
        if not self.position and self.data.close > self.bb.lines.top:
            self.buy()
        elif self.position and self.data.close < self.bb.lines.bot:
            self.sell()


class RsiMeanReversion(bt.Strategy):
    """RSI 均值回归策略"""

    params = (
        ("rsi_period", 14),
        ("rsi_lower", 30),
        ("rsi_upper", 70),
    )

    def __init__(self):
        self.rsi = bt.ind.RSI(self.data.close, period=self.p.rsi_period)

    def next(self):
        if not self.position and self.rsi < self.p.rsi_lower:
            self.buy()
        elif self.position and self.rsi > self.p.rsi_upper:
            self.sell()


class SmaCross(bt.Strategy):
    """双移动平均线交叉策略"""

    params = (
        ("ma_short", 10),
        ("ma_long", 30),
    )

    def __init__(self):
        self.ma_short = bt.ind.SMA(self.data.close, period=self.p.ma_short)
        self.ma_long = bt.ind.SMA(self.data.close, period=self.p.ma_long)
        self.crossover = bt.ind.CrossOver(self.ma_short, self.ma_long)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.sell()
