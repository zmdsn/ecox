"""
股票基础信息维护模块
使用 akshare 获取 A 股基础信息，并使用 ORM 存储到数据库
"""
import warnings
warnings.filterwarnings("ignore")

import akshare as ak
import pandas as pd
import time
import logging
from logging import FileHandler
from datetime import datetime, date
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import List, Dict, Any

# 导入服务和数据库模块
from ..services import StockService, DataCollectionService
from ..database import get_db_session
from .. import models

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("a_share_basic_maintain.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 接口配置
CALL_INTERVAL = 1  # 单股票详情查询间隔（反爬）
MAX_RETRIES = 3    # 数据库/接口重试次数


def initialize_database():
    """初始化数据库表结构"""
    from ..database import init_db

    try:
        db = init_db()
        db.get_engine()
        logger.info("a_share_basic 表结构初始化/验证成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_stock_basic_raw() -> pd.DataFrame:
    """从 ak.stock_info_a_code_name() 获取全量A股代码+名称"""
    try:
        df = ak.stock_info_a_code_name()
        logger.info(f"从 stock_info_a_code_name() 获取到 {len(df)} 条A股基础记录")

        df.rename(
            columns={
                "code": "stock_code",
                "name": "stock_name"
            },
            inplace=True
        )

        df = df[["stock_code", "stock_name"]].dropna()
        df = df[df["stock_code"].str.match(r"^\d{6}$")]
        df = df.drop_duplicates(subset=["stock_code"])

        logger.info(f"清洗后有效A股记录数：{len(df)}")
        return df
    except Exception as e:
        logger.error(f"获取 stock_info_a_code_name() 失败：{e}", exc_info=True)
        raise


def supplement_stock_detail(raw_df: pd.DataFrame) -> pd.DataFrame:
    """为基础代码表补充行业、上市日期等详情"""
    detail_list = []
    total = len(raw_df)
    logger.info(f"开始为 {total} 只股票补充行业/上市日期详情")

    for idx, row in raw_df.iterrows():
        stock_code = row["stock_code"]
        stock_name = row["stock_name"]

        industry = None
        list_date = None
        delist_date = None

        try:
            detail_df = ak.stock_individual_info_em(symbol=stock_code)
            detail_df.columns = ["key", "value"]

            industry_row = detail_df[detail_df["key"] == "申万一级行业"]
            if not industry_row.empty:
                industry = industry_row["value"].values[0]

            list_date_row = detail_df[detail_df["key"] == "上市日期"]
            if not list_date_row.empty:
                list_date_str = list_date_row["value"].values[0]
                list_date = datetime.strptime(list_date_str, "%Y-%m-%d").date()

            if (idx + 1) % 50 == 0:
                logger.info(f"补充详情进度：{idx+1}/{total} | 当前股票：{stock_code} {stock_name}")

        except Exception as e:
            logger.warning(f"[{stock_code}] 补充详情失败：{e}")

        detail_list.append({
            "stock_code": stock_code,
            "stock_name": stock_name,
            "industry": industry,
            "list_date": list_date,
            "delist_date": delist_date
        })
        time.sleep(CALL_INTERVAL)

    detail_df = pd.DataFrame(detail_list)
    logger.info(f"股票详情补充完成，有效记录数：{len(detail_df)}")
    return detail_df


def sync_a_share_basic() -> Dict[str, int]:
    """增量同步a_share_basic表（基于stock_info_a_code_name()）"""
    start_time = datetime.now()
    logger.info("===== 开始增量同步a_share_basic表 =====")

    new_count = 0
    update_count = 0

    try:
        raw_df = get_stock_basic_raw()
        if raw_df.empty:
            logger.warning("未获取到有效A股基础数据，同步终止")
            return {"new": 0, "update": 0}

        # 获取已存在的股票代码
        with get_db_session() as session:
            exist_codes = [
                row[0] for row in session.query(models.StockBasic.stock_code).all()
            ]
            logger.info(f"数据库已有A股记录数：{len(exist_codes)}")

        stock_service = StockService()

        # 处理新增股票
        new_df = raw_df[~raw_df["stock_code"].isin(exist_codes)]
        new_count = len(new_df)

        for _, row in new_df.iterrows():
            try:
                stock_service.save_stock_info(
                    stock_code=row["stock_code"],
                    stock_name=row["stock_name"],
                    list_date=None,
                )
            except Exception as e:
                logger.warning(f"新增股票 {row['stock_code']} 失败: {e}")

        # 处理更新股票
        update_df = raw_df[raw_df["stock_code"].isin(exist_codes)]
        update_count = len(update_df)

        for _, row in update_df.iterrows():
            try:
                stock_service.save_stock_info(
                    stock_code=row["stock_code"],
                    stock_name=row["stock_name"],
                )
            except Exception as e:
                logger.warning(f"更新股票 {row['stock_code']} 失败: {e}")

        cost = (datetime.now() - start_time).total_seconds()
        logger.info(f"===== 同步完成 | 新增{new_count}条 | 更新{update_count}条 | 耗时{cost:.2f}秒 =====")

        return {"new": new_count, "update": update_count}

    except Exception as e:
        logger.error(f"同步失败：{e}", exc_info=True)
        raise


def validate_a_share_basic() -> Dict[str, Any]:
    """校验a_share_basic表数据完整性"""
    logger.info("===== 开始校验a_share_basic表 =====")

    result = {
        "duplicates": 0,
        "invalid_dates": 0,
        "empty_names": 0,
    }

    try:
        with get_db_session() as session:
            # 检查重复代码
            from sqlalchemy import func
            duplicates = session.query(
                models.StockBasic.stock_code,
                func.count(models.StockBasic.stock_code)
            ).group_by(
                models.StockBasic.stock_code
            ).having(
                func.count(models.StockBasic.stock_code) > 1
            ).all()

            result["duplicates"] = len(duplicates)
            if duplicates:
                logger.warning(f"发现{len(duplicates)}个重复代码：{duplicates}")
                # ORM 模型使用主键约束，通常不会出现重复
                logger.info("请检查数据库约束是否正确")
            else:
                logger.info("无重复主键数据")

            # 检查无效上市日期
            from datetime import datetime
            invalid_dates = session.query(models.StockBasic).filter(
                models.StockBasic.list_date > datetime.now().date()
            ).all()

            result["invalid_dates"] = len(invalid_dates)
            if invalid_dates:
                codes = [s.stock_code for s in invalid_dates[:10]]
                logger.warning(f"发现{len(invalid_dates)}个无效上市日期：{codes}...")
            else:
                logger.info("上市日期格式校验通过")

            # 检查空名称
            empty_names = session.query(models.StockBasic).filter(
                (models.StockBasic.stock_name.is_(None)) |
                (models.StockBasic.stock_name == '')
            ).all()

            result["empty_names"] = len(empty_names)
            if empty_names:
                codes = [s.stock_code for s in empty_names[:10]]
                logger.warning(f"发现{len(empty_names)}个空名称股票：{codes}...")
            else:
                logger.info("股票名称非空校验通过")

        logger.info("===== a_share_basic表校验完成 =====")
        return result

    except Exception as e:
        logger.error(f"校验失败：{e}", exc_info=True)
        raise


def start_scheduled_maintain():
    """启动定时维护（每日同步+每周校验）"""
    initialize_database()

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    logger.info("启动a_share_basic表定时维护调度器")

    scheduler.add_job(
        func=sync_a_share_basic,
        trigger=CronTrigger(hour=6, minute=0, timezone="Asia/Shanghai"),
        id="sync_a_share_basic_daily",
        replace_existing=True
    )

    scheduler.add_job(
        func=validate_a_share_basic,
        trigger=CronTrigger(day_of_week=0, hour=8, minute=0, timezone="Asia/Shanghai"),
        id="validate_a_share_basic_weekly",
        replace_existing=True
    )

    logger.info("定时任务列表：")
    for job in scheduler.get_jobs():
        logger.info(f"- {job.id}：{job.trigger}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("手动终止调度器")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"调度器异常：{e}", exc_info=True)
        scheduler.shutdown()


if __name__ == "__main__":
    initialize_database()
    sync_a_share_basic()
    validate_a_share_basic()
    # start_scheduled_maintain()
