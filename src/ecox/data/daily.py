"""
日线数据采集模块
使用 akshare 获取 A 股历史日线数据，并使用 ORM 存储到数据库
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

# 导入服务和数据库模块
from ..services import DataCollectionService, StockService
from ..database import get_db_session
from .. import models

ADJUST_TYPE = "qfq"  # 复权类型
REQUEST_DELAY = 0.5  # 请求间隔(秒)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("daily_data.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def initialize_database():
    """初始化数据库表结构"""
    from ..database import init_db

    try:
        db = init_db()
        db.create_all()
        logger.info("数据库表结构初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_active_stocks():
    """获取当前活跃的股票列表及最后更新日期"""
    with get_db_session() as session:
        try:
            # 检查表是否存在，如果不存在则返回空
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            if 'a_share_basic' not in inspector.get_table_names():
                logger.warning("a_share_basic 表不存在")
                return pd.DataFrame()

            query = session.query(
                models.StockBasic.stock_code,
                models.StockBasic.list_date,
            ).filter(
                models.StockBasic.delist_date.is_(None)
            ).order_by(models.StockBasic.stock_code)

            df = pd.read_sql_query(query.statement, session.bind)
            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()


def fetch_single_stock_daily(stock_code, start_date):
    """获取单只股票日线数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=datetime.now().strftime('%Y%m%d'),
            adjust=ADJUST_TYPE
        )

        if df.empty:
            return None

        df = df.rename(columns={
            '日期': 'trade_date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'
        })

        df['stock_code'] = stock_code
        df['adjust_flag'] = ADJUST_TYPE
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        return df[['stock_code', 'trade_date', 'open', 'close',
                   'high', 'low', 'volume', 'amount', 'adjust_flag']]

    except Exception as e:
        logger.error(f"获取 {stock_code} 数据失败: {e}")
        return None


def get_latest_trade_date(stock_code):
    """获取股票最后更新的交易日期"""
    with get_db_session() as session:
        try:
            latest = session.query(models.StockDailyData.trade_date).filter(
                models.StockDailyData.stock_code == stock_code,
                models.StockDailyData.adjust_flag == ADJUST_TYPE
            ).order_by(models.StockDailyData.trade_date.desc()).first()

            return latest[0] if latest else None

        except Exception as e:
            logger.error(f"获取 {stock_code} 最后更新日期失败: {e}")
            return None


def update_daily_data_for_stock(stock_code, list_date):
    """为单只股票更新日线数据"""
    # 获取最后更新日期
    last_date = get_latest_trade_date(stock_code)

    if last_date is None:
        # 首次获取，从上市日期开始
        if pd.isna(list_date) or list_date is None:
            start_date_str = "19901219"
        else:
            start_date_str = list_date.strftime('%Y%m%d')
    else:
        # 增量更新，从最后日期+1天开始
        start_date = last_date + timedelta(days=1)
        start_date_str = start_date.strftime('%Y%m%d')

    logger.info(f"更新 {stock_code}，从 {start_date_str} 开始")

    new_data_df = fetch_single_stock_daily(stock_code, start_date_str)

    if new_data_df is None or new_data_df.empty:
        return True, 0

    try:
        service = DataCollectionService()

        # 转换 DataFrame 为字典列表
        data_list = []
        for _, row in new_data_df.iterrows():
            data = {
                "stock_code": row["stock_code"],
                "trade_date": row["trade_date"].to_pydatetime(),
                "open": float(row["open"]) if pd.notna(row["open"]) else None,
                "close": float(row["close"]) if pd.notna(row["close"]) else None,
                "high": float(row["high"]) if pd.notna(row["high"]) else None,
                "low": float(row["low"]) if pd.notna(row["low"]) else None,
                "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                "amount": float(row["amount"]) if pd.notna(row["amount"]) else None,
                "adjust_flag": row["adjust_flag"],
            }
            data_list.append(data)

        result = service.save_daily_data(data_list)
        new_rows = result.get("new", 0)

        logger.info(f"{stock_code}: 成功插入 {new_rows} 行新数据")
        return True, new_rows

    except Exception as e:
        logger.error(f"{stock_code}: 数据入库失败 - {e}")
        return False, 0


def update_stock_list():
    """更新股票基本信息表"""
    logger.info("开始更新股票列表...")
    try:
        stock_info_df = ak.stock_info_a_code_name()
        if stock_info_df.empty:
            return

        stock_info_df = stock_info_df.rename(columns={
            'code': 'stock_code', 'name': 'stock_name'
        })

        service = StockService()

        # 批量保存股票信息
        for _, row in stock_info_df.iterrows():
            service.save_stock_info(
                stock_code=row['stock_code'],
                stock_name=row['stock_name'],
                list_date=None,  # 可以后续补充
            )

        logger.info(f"股票列表更新完成，共处理 {len(stock_info_df)} 只股票")

    except Exception as e:
        logger.error(f"更新股票列表失败: {e}")


def main_daily_update():
    """每日增量更新的主函数（自动初始化数据库）"""
    logger.info("=" * 60)
    logger.info("股票数据自动化更新系统启动")
    logger.info("=" * 60)

    try:
        initialize_database()
        update_stock_list()

        stocks_df = get_active_stocks()
        if stocks_df.empty:
            logger.warning("股票列表为空，将在下次运行时获取")
            return

        logger.info(f"共发现 {len(stocks_df)} 只活跃股票需要更新")

        total_success = 0
        total_failed = 0
        total_new_rows = 0

        for idx, row in stocks_df.iterrows():
            success, new_rows = update_daily_data_for_stock(
                row['stock_code'], row['list_date']
            )

            if success:
                total_success += 1
                total_new_rows += new_rows
            else:
                total_failed += 1

            time.sleep(REQUEST_DELAY)

            if (idx + 1) % 50 == 0:
                logger.info(f"进度: {idx + 1}/{len(stocks_df)} | 成功: {total_success} | 失败: {total_failed}")

        logger.info("=" * 60)
        logger.info("更新任务完成！")
        logger.info(f"成功更新: {total_success} 只股票")
        logger.info(f"更新失败: {total_failed} 只股票")
        logger.info(f"新增数据: {total_new_rows} 行")

        # 记录更新日志
        service = DataCollectionService()
        service.log_update(
            success_count=total_success,
            failed_count=total_failed,
            new_rows_count=total_new_rows,
        )
        logger.info("运行日志已保存")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"更新过程发生错误: {e}")

        # 记录错误日志
        service = DataCollectionService()
        service.log_update(
            success_count=0,
            failed_count=0,
            new_rows_count=0,
            error_message=str(e),
        )


def initial_full_load():
    """首次全量数据拉取（谨慎使用）"""
    logger.warning("=" * 60)
    logger.warning("首次全量数据拉取模式")
    logger.warning("这将非常耗时，建议在网络稳定时运行")
    logger.warning("=" * 60)

    try:
        initialize_database()
        update_stock_list()

        stocks_df = get_active_stocks()
        logger.info(f"将为 {len(stocks_df)} 只股票拉取全部历史数据...")

        for idx, row in stocks_df.iterrows():
            stock_code = row['stock_code']

            logger.info(f"[{idx + 1}/{len(stocks_df)}] 拉取 {stock_code} 全量数据")

            success, new_rows = update_daily_data_for_stock(
                stock_code, None
            )

            time.sleep(REQUEST_DELAY)

            if (idx + 1) % 10 == 0:
                logger.info(f"全量拉取进度: {idx + 1}/{len(stocks_df)}")

    except Exception as e:
        logger.error(f"全量拉取失败: {e}")


if __name__ == "__main__":
    main_daily_update()
