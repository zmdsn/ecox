# ========== 第一步：过滤弃用警告 ==========
import pandas_market_calendars as mcal
from datetime import datetime, date
import pytz
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
from psycopg2 import OperationalError, ProgrammingError
from datetime import datetime
import time
import pandas as pd
import psycopg2.extras
import psycopg2
import akshare as ak
import warnings
warnings.filterwarnings("ignore", category=UserWarning,
                        message="pkg_resources is deprecated as an API.*")
warnings.filterwarnings("ignore", category=DeprecationWarning,
                        message="License classifiers are deprecated.*")

# ========== 核心依赖导入 ==========

# ========== 配置项 ==========
# PostgreSQL 连接配置（替换为你的实际信息）
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "zmdsn",
    "password": "zmdsnsdmz",
    "database": "stock",
    "options": "-c client_encoding=utf8"
}
# 调用间隔（秒），遵循反爬安全频率
CALL_INTERVAL = 360
# 股票范围：None=全市场，指定如["600000", "000001"]
STOCK_CODES = None

# ========== 数据库操作 ==========


def get_pg_connection():
    """创建PostgreSQL连接（带重连机制）"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = False
        return conn
    except OperationalError as e:
        print(f"PostgreSQL连接失败：{e}")
        time.sleep(5)
        return get_pg_connection()


def create_stock_table():
    """创建A股实时表（修复COMMENT语法，兼容所有PostgreSQL版本）"""
    conn = get_pg_connection()
    cursor = conn.cursor()
    # 1. 建表（无注释）
    create_sql = """
    CREATE TABLE IF NOT EXISTS a_share_real_time (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        latest_price NUMERIC(10,2),
        price_change NUMERIC(10,2),
        price_change_rate NUMERIC(10,2),
        volume BIGINT,
        turnover BIGINT,
        high_price NUMERIC(10,2),
        low_price NUMERIC(10,2),
        open_price NUMERIC(10,2),
        pre_close_price NUMERIC(10,2),
        update_time TIMESTAMP NOT NULL,
        CONSTRAINT idx_code_time UNIQUE (stock_code, update_time)
    );
    """
    # 2. 批量添加注释
    comment_sqls = [
        "COMMENT ON COLUMN a_share_real_time.latest_price IS '最新价';",
        "COMMENT ON COLUMN a_share_real_time.price_change IS '涨跌额';",
        "COMMENT ON COLUMN a_share_real_time.price_change_rate IS '涨跌幅(%)';",
        "COMMENT ON COLUMN a_share_real_time.volume IS '成交量(手)';",
        "COMMENT ON COLUMN a_share_real_time.turnover IS '成交额(万元)';",
        "COMMENT ON COLUMN a_share_real_time.high_price IS '最高价';",
        "COMMENT ON COLUMN a_share_real_time.low_price IS '最低价';",
        "COMMENT ON COLUMN a_share_real_time.open_price IS '今开价';",
        "COMMENT ON COLUMN a_share_real_time.pre_close_price IS '昨收价';",
        "COMMENT ON COLUMN a_share_real_time.update_time IS '数据更新时间';",
        "COMMENT ON TABLE a_share_real_time IS 'A股实时行情表';"
    ]
    try:
        cursor.execute(create_sql)
        for sql in comment_sqls:
            cursor.execute(sql)
        conn.commit()
        print("数据表创建+注释添加成功")
    except ProgrammingError as e:
        conn.rollback()
        print(f"创建表失败：{e}")
    finally:
        cursor.close()
        conn.close()


def insert_stock_data(df):
    """批量插入数据（忽略重复）"""
    if df.empty:
        print("无数据可插入")
        return
    conn = get_pg_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT INTO a_share_real_time (
        stock_code, stock_name, latest_price, price_change, price_change_rate,
        volume, turnover, high_price, low_price, open_price, pre_close_price, update_time
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (stock_code, update_time) DO NOTHING;
    """
    data_list = []
    update_time = datetime.now()
    for _, row in df.iterrows():
        # 字段值类型转换（避免插入报错）
        data_tuple = (
            str(row.get("代码")),
            str(row.get("名称")),
            float(row.get("最新价", 0)),
            float(row.get("涨跌额", 0)),
            float(row.get("涨跌幅", 0)),
            int(row.get("成交量", 0)),
            int(row.get("成交额", 0)),
            float(row.get("最高价", 0)),
            float(row.get("最低价", 0)),
            float(row.get("今开价", 0)),
            float(row.get("昨收价", 0)),
            update_time
        )
        data_list.append(data_tuple)
    try:
        # 批量插入优化
        batch_size = 100
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i+batch_size]
            psycopg2.extras.execute_batch(cursor, insert_sql, batch)
        conn.commit()
        print(f"成功新增 {cursor.rowcount} 条数据")
    except Exception as e:
        conn.rollback()
        print(f"插入失败：{e}")
    finally:
        cursor.close()
        conn.close()

# ========== 数据获取（替换失效接口） ==========


def get_a_share_real_time_data():
    """获取A股实时数据（使用最新的em接口，替代失效的stock_zh_a_spot()）"""
    try:
        if STOCK_CODES is None:
            # 全市场A股行情（最新有效接口）
            df = ak.stock_zh_a_spot()
        else:
            # 指定股票批量获取
            df_list = []
            for code in STOCK_CODES:
                # 单股票行情（em接口兼容symbol参数）
                df_single = ak.stock_zh_a_spot_em(symbol=code)
                df_list.append(df_single)
                time.sleep(CALL_INTERVAL)
            df = pd.concat(df_list, ignore_index=True)

        # 字段校验：确保核心字段存在（避免接口字段更新导致报错）
        core_columns = ["代码", "名称", "最新价", "涨跌额",
                        "涨跌幅", "成交量", "成交额", "最高", "最低", "今开", "昨收"]
        missing_cols = [col for col in core_columns if col not in df.columns]
        if missing_cols:
            print(f"警告：接口字段缺失 {missing_cols}，请核对akshare最新字段！")
            return pd.DataFrame()
        df["代码"] = df["代码"].astype(str).str[-6:]  # 补全股票代码至6位
        # 数据清洗
        df = df[core_columns].dropna()
        df = df[df["最新价"] > 0]
        return df
    except Exception as e:
        print(f"获取数据失败：{e}")
        return pd.DataFrame()


def is_a_stock_trading_time() -> bool:
    """
    完整判断：当前是否为A股交易日且在交易时段内。
    返回: bool
    """
    # 1. 获取当前北京时间及日期
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    beijing_now = datetime.now(shanghai_tz)
    beijing_date = beijing_now.date()
    current_time = beijing_now.hour * 100 + beijing_now.minute

    # 2. 获取A股交易日历并判断是否为交易日
    # 创建上海证券交易所日历对象
    sse_calendar = mcal.get_calendar('SSE')
    # 获取当天（基于本地时区）的交易日程，格式为UTC时间，所以我们需要用北京时间日期去查询
    schedule = sse_calendar.schedule(
        start_date=beijing_date, end_date=beijing_date)
    # 如果schedule为空，说明当天不是交易日
    is_trading_day = not schedule.empty

    if not is_trading_day:
        return False

    # 3. 如果是交易日，再判断是否在交易时段内
    morning_start = 930
    morning_end = 1130
    afternoon_start = 1300
    afternoon_end = 1500

    is_in_trading_hours = (morning_start <= current_time <= morning_end) or \
                          (afternoon_start <= current_time <= afternoon_end)
    return is_in_trading_hours


def fetch_job():
    """定时任务要执行的函数"""
    print(f"✅ [{datetime.now()}] 定时触发抓取...")
    try:
        stock_df = get_a_share_real_time_data()
        if not stock_df.empty:
            insert_stock_data(stock_df)
    except Exception as e:
        print(f"❌ 抓取失败: {e}")


def run_job():
    # 创建调度器
    scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Shanghai'))

    # 添加任务：在交易时段的每分钟执行（可根据需要调整）
    # Cron表达式解释：在每小时的每分钟执行，但仅限于9-11点和13-14点之间

    # 触发器1：9-11、13-14点每6分钟触发（原有逻辑）
    trigger_normal = CronTrigger(
        second=0,  # 固定整分钟触发，避免秒级偏差
        minute='*/5',
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )

    # 触发器2：15点0分单独触发（补充收盘数据）
    trigger_1500 = CronTrigger(
        second=0,
        minute=0,
        hour=15,
        timezone='Asia/Shanghai'
    )
    scheduler.add_job(
        fetch_job,
        trigger_normal,
        second=0,
        id='trigger_normal',
        name='获取A股实时数据',
    )
    # scheduler.add_job(
    #     fetch_job,
    #     trigger_1500,
    #     second=0,
    #     id='trigger_1500',
    #     name='获取A股实时数据',
    # )

    # 注意：这行代码会阻塞主线程，使调度器开始工作
    print("🚀 调度器已启动，等待下一个任务触发时间...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("🛑 调度器已手动停止。")


# ========== 主程序 ==========
if __name__ == "__main__":
    # 初始化数据表
    create_stock_table()
    run_job()
    # uv run watchfiles "uv run get_data.py" get_data.py
