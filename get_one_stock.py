import akshare as ak
import pandas as pd
from datetime import datetime

def get_stock_data(symbol="000001", start_date="20200101", end_date="20231231"):
    """
    使用 akshare 获取 A 股历史数据
    :param symbol: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: DataFrame
    """
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
    print(df.head(2))
    df['datetime'] = pd.to_datetime(df['日期'])
    df.set_index('datetime', inplace=True)
    df.rename(columns={'开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}, inplace=True)
    df['openinterest'] = 0
    return df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]