"""
实时行情数据采集模块
使用 akshare 获取 A 股实时行情数据，并使用 ORM 存储到数据库
"""
import pandas_market_calendars as mcal
from datetime import datetime
import pytz
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import pandas as pd
import akshare as ak
import warnings
import logging

warnings.filterwarnings("ignore", category=UserWarning,
                        message="pkg_resources is deprecated as an API.*")
warnings.filterwarnings("ignore", category=DeprecationWarning,
                        message="License classifiers are deprecated.*")

# 导入服务和配置
from ..services import DataCollectionService, StockService
from ..config import PG_CONFIG

# 调用间隔（秒），遵循反爬安全频率
CALL_INTERVAL = 360
# 股票范围：None=全市场，指定如["600000", "000001"]
STOCK_CODES = None

# 日志配置
logger = logging.getLogger(__name__)


def initialize_database():
    """初始化数据库表结构"""
    from ..database import init_db
    from .. import models

    try:
        db = init_db()
        db.create_all()
        logger.info("数据库表结构初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def insert_stock_data(df):
    """使用 ORM 批量插入数据"""
    if df.empty:
        logger.warning("无数据可插入")
        return {"success": 0, "failed": 0}

    service = DataCollectionService()

    # 转换 DataFrame 为字典列表
    data_list = []
    update_time = datetime.now()

    for _, row in df.iterrows():
        data = {
            "stock_code": str(row.get("代码")),
            "stock_name": str(row.get("名称")),
            "latest_price": float(row.get("最新价", 0)),
            "price_change": float(row.get("涨跌额", 0)),
            "price_change_rate": float(row.get("涨跌幅", 0)),
            "volume": int(row.get("成交量", 0)),
            "turnover": int(row.get("成交额", 0)),
            "high_price": float(row.get("最高", 0)),
            "low_price": float(row.get("最低", 0)),
            "open_price": float(row.get("今开", 0)),
            "pre_close_price": float(row.get("昨收", 0)),
        }
        data_list.append(data)

    result = service.save_realtime_data(data_list)
    logger.info(f"保存完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")

    return result


def get_a_share_real_time_data():
    """获取A股实时数据（使用最新的em接口）"""
    try:
        if STOCK_CODES is None:
            df = ak.stock_zh_a_spot()
        else:
            df_list = []
            for code in STOCK_CODES:
                df_single = ak.stock_zh_a_spot_em(symbol=code)
                df_list.append(df_single)
                time.sleep(CALL_INTERVAL)
            df = pd.concat(df_list, ignore_index=True)

        core_columns = ["代码", "名称", "最新价", "涨跌额",
                        "涨跌幅", "成交量", "成交额", "最高", "最低", "今开", "昨收"]
        missing_cols = [col for col in core_columns if col not in df.columns]
        if missing_cols:
            logger.warning(f"接口字段缺失 {missing_cols}，请核对akshare最新字段！")
            return pd.DataFrame()
        df["代码"] = df["代码"].astype(str).str[-6:]
        df = df[core_columns].dropna()
        df = df[df["最新价"] > 0]
        return df
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return pd.DataFrame()


def is_a_stock_trading_time() -> bool:
    """判断当前是否为A股交易日且在交易时段内"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    beijing_now = datetime.now(shanghai_tz)
    beijing_date = beijing_now.date()
    current_time = beijing_now.hour * 100 + beijing_now.minute

    sse_calendar = mcal.get_calendar('SSE')
    schedule = sse_calendar.schedule(
        start_date=beijing_date, end_date=beijing_date)
    is_trading_day = not schedule.empty

    if not is_trading_day:
        return False

    morning_start = 930
    morning_end = 1130
    afternoon_start = 1300
    afternoon_end = 1500

    is_in_trading_hours = (morning_start <= current_time <= morning_end) or \
                          (afternoon_start <= current_time <= afternoon_end)
    return is_in_trading_hours


def fetch_job():
    """定时任务要执行的函数"""
    logger.info(f"[{datetime.now()}] 定时触发抓取...")
    try:
        stock_df = get_a_share_real_time_data()
        if not stock_df.empty:
            result = insert_stock_data(stock_df)

            # 记录更新日志
            service = DataCollectionService()
            service.log_update(
                success_count=result['success'],
                failed_count=result['failed'],
                new_rows_count=result['success'],
            )
    except Exception as e:
        logger.error(f"抓取失败: {e}")

        # 记录错误日志
        service = DataCollectionService()
        service.log_update(
            success_count=0,
            failed_count=0,
            new_rows_count=0,
            error_message=str(e),
        )


def run_job():
    """启动实时行情调度器"""
    scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Shanghai'))

    trigger_normal = CronTrigger(
        second=0,
        minute='*/15',
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )

    scheduler.add_job(
        fetch_job,
        trigger_normal,
        second=0,
        id='trigger_normal',
        name='获取A股实时数据',
    )

    logger.info("调度器已启动，等待下一个任务触发时间...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器已手动停止。")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    initialize_database()
    run_job()
