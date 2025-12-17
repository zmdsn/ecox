import warnings
warnings.filterwarnings("ignore")

import akshare as ak
import psycopg2
import psycopg2.extras
import pandas as pd
import time
import logging
from datetime import datetime, date
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# ========== 1. 基础配置 ==========
# PostgreSQL 连接配置（替换为你的实际配置）
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "zmdsn",
    "password": "zmdsnsdmz",
    "database": "stock",
    "options": "-c client_encoding=utf8"
}

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

# ========== 2. 数据库核心操作 ==========
def get_pg_conn():
    """创建PostgreSQL连接（带重连）"""
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            conn.autocommit = False
            logger.info("数据库连接成功")
            return conn
        except psycopg2.OperationalError as e:
            retry_count += 1
            logger.error(f"数据库连接失败（重试{retry_count}/{MAX_RETRIES}）：{e}")
            time.sleep(5)
    raise Exception("数据库多次连接失败，终止任务")

def init_a_share_basic_table():
    """初始化a_share_basic表结构"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS a_share_basic (
        stock_code VARCHAR(20) PRIMARY KEY,  -- 6位A股代码（主键）
        stock_name VARCHAR(50) NOT NULL,     -- 股票名称
        industry VARCHAR(50),                -- 申万一级行业
        list_date DATE,                      -- 上市日期
        delist_date DATE,                    -- 退市日期（NULL=未退市）
        update_time TIMESTAMP DEFAULT NOW()  -- 最后更新时间
    );
    COMMENT ON TABLE a_share_basic IS 'A股基础信息表（核心维度）';
    COMMENT ON COLUMN a_share_basic.stock_code IS '6位数字A股代码';
    COMMENT ON COLUMN a_share_basic.stock_name IS '股票简称';
    COMMENT ON COLUMN a_share_basic.industry IS '申万一级行业分类';
    COMMENT ON COLUMN a_share_basic.list_date IS '股票上市日期';
    COMMENT ON COLUMN a_share_basic.delist_date IS '退市日期（未退市则为NULL）';
    COMMENT ON COLUMN a_share_basic.update_time IS '记录最后更新时间';
    """
    try:
        conn = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()
        logger.info("a_share_basic表结构初始化/验证成功")
    except Exception as e:
        conn.rollback()
        logger.error(f"表初始化失败：{e}", exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()

# ========== 3. 基于 stock_info_a_code_name() 获取基础数据 ==========
def get_stock_basic_raw():
    """核心：从 ak.stock_info_a_code_name() 获取全量A股代码+名称"""
    try:
        # 核心接口：获取A股代码名称基础表
        df = ak.stock_info_a_code_name()
        logger.info(f"从 stock_info_a_code_name() 获取到 {len(df)} 条A股基础记录")
        
        # 字段重命名（统一为后续逻辑的字段名）
        df.rename(
            columns={
                "code": "stock_code",  # 接口返回的代码字段
                "name": "stock_name"   # 接口返回的名称字段
            },
            inplace=True
        )
        
        # 数据清洗：仅保留6位数字代码、去空、去重
        df = df[["stock_code", "stock_name"]].dropna()
        df = df[df["stock_code"].str.match(r"^\d{6}$")]  # 过滤6位数字代码
        df = df.drop_duplicates(subset=["stock_code"])   # 去重
        
        logger.info(f"清洗后有效A股记录数：{len(df)}")
        return df
    except Exception as e:
        logger.error(f"获取 stock_info_a_code_name() 失败：{e}", exc_info=True)
        raise

def supplement_stock_detail(raw_df):
    """为基础代码表补充行业、上市日期等详情"""
    detail_list = []
    total = len(raw_df)
    logger.info(f"开始为 {total} 只股票补充行业/上市日期详情")
    
    for idx, row in raw_df.iterrows():
        stock_code = row["stock_code"]
        stock_name = row["stock_name"]
        
        # 初始化默认值
        industry = None
        list_date = None
        delist_date = None
        
        try:
            # 调用单股票详情接口补充字段
            detail_df = ak.stock_individual_info_em(symbol=stock_code)
            detail_df.columns = ["key", "value"]  # 统一字段名
            
            # 提取申万一级行业
            industry_row = detail_df[detail_df["key"] == "申万一级行业"]
            if not industry_row.empty:
                industry = industry_row["value"].values[0]
            
            # 提取上市日期并转换为DATE类型
            list_date_row = detail_df[detail_df["key"] == "上市日期"]
            if not list_date_row.empty:
                list_date_str = list_date_row["value"].values[0]
                list_date = datetime.strptime(list_date_str, "%Y-%m-%d").date()
            
            # 退市日期暂默认NULL（可扩展接口补充）
            delist_date = None
            
            # 进度日志
            if (idx + 1) % 50 == 0:
                logger.info(f"补充详情进度：{idx+1}/{total} | 当前股票：{stock_code} {stock_name}")
        
        except Exception as e:
            logger.warning(f"[{stock_code}] 补充详情失败：{e}")
        
        # 追加到结果列表
        detail_list.append({
            "stock_code": stock_code,
            "stock_name": stock_name,
            "industry": industry,
            "list_date": list_date,
            "delist_date": delist_date
        })
        time.sleep(CALL_INTERVAL)  # 反爬间隔
    
    # 转换为DataFrame
    detail_df = pd.DataFrame(detail_list)
    logger.info(f"股票详情补充完成，有效记录数：{len(detail_df)}")
    return detail_df

# ========== 4. 增量同步核心逻辑 ==========
def sync_a_share_basic():
    """增量同步a_share_basic表（基于stock_info_a_code_name()）"""
    start_time = datetime.now()
    logger.info("===== 开始增量同步a_share_basic表 =====")
    
    try:
        # 步骤1：获取基础代码+名称
        raw_df = get_stock_basic_raw()
        if raw_df.empty:
            logger.warning("未获取到有效A股基础数据，同步终止")
            return
        
        # 步骤2：补充行业、上市日期等详情
        # full_df = supplement_stock_detail(raw_df)
        full_df = raw_df
        full_df["industry"] = None
        full_df["list_date"] = None
        full_df["delist_date"] = None   

        # 步骤3：查询数据库已有代码
        conn = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT stock_code FROM a_share_basic;")
        exist_codes = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库已有A股记录数：{len(exist_codes)}")
        
        # 步骤4：新增数据（数据库不存在的代码）
        new_df = full_df[~full_df["stock_code"].isin(exist_codes)]
        new_count = len(new_df)
        if new_count > 0:
            insert_sql = """
            INSERT INTO a_share_basic (stock_code, stock_name, industry, list_date, delist_date)
            VALUES (%s, %s, %s, %s, %s);
            """
            insert_data = [
                (row["stock_code"], row["stock_name"], row["industry"], row["list_date"], row["delist_date"])
                for _, row in new_df.iterrows()
            ]
            # 批量插入（每页100条）
            psycopg2.extras.execute_batch(cursor, insert_sql, insert_data, page_size=100)
            logger.info(f"新增A股记录数：{new_count}")
        
        # 步骤5：更新存量数据（名称/行业/上市日期变更）
        update_df = full_df[full_df["stock_code"].isin(exist_codes)]
        update_count = len(update_df)
        if update_count > 0:
            update_sql = """
            UPDATE a_share_basic 
            SET stock_name=%s, industry=%s, list_date=%s, delist_date=%s, update_time=NOW()
            WHERE stock_code=%s;
            """
            update_data = [
                (row["stock_name"], row["industry"], row["list_date"], row["delist_date"], row["stock_code"])
                for _, row in update_df.iterrows()
            ]
            # 批量更新
            psycopg2.extras.execute_batch(cursor, update_sql, update_data, page_size=100)
            logger.info(f"更新A股记录数：{update_count}")
        
        # 提交事务
        conn.commit()
        cost = (datetime.now() - start_time).total_seconds()
        logger.info(f"===== 同步完成 | 新增{new_count}条 | 更新{update_count}条 | 耗时{cost:.2f}秒 =====")
    
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"同步失败：{e}", exc_info=True)
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ========== 5. 数据校验 ==========
def validate_a_share_basic():
    """校验a_share_basic表数据完整性"""
    logger.info("===== 开始校验a_share_basic表 =====")
    try:
        conn = get_pg_conn()
        cursor = conn.cursor()
        
        # 校验1：主键重复（兜底检查）
        cursor.execute("""
        SELECT stock_code, COUNT(*) FROM a_share_basic GROUP BY stock_code HAVING COUNT(*) > 1;
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            logger.warning(f"发现{len(duplicates)}个重复代码：{duplicates}")
            # 清理重复数据（保留第一条）
            for code, _ in duplicates:
                cursor.execute("""
                DELETE FROM a_share_basic WHERE stock_code=%s AND ctid NOT IN (
                    SELECT MIN(ctid) FROM a_share_basic WHERE stock_code=%s
                );
                """, (code, code))
            conn.commit()
            logger.info("重复数据已清理")
        else:
            logger.info("✅ 无重复主键数据")
        
        # 校验2：上市日期有效性（不晚于当前日期）
        cursor.execute("""
        SELECT stock_code, list_date FROM a_share_basic 
        WHERE list_date IS NOT NULL AND list_date > CURRENT_DATE;
        """)
        invalid_dates = cursor.fetchall()
        if invalid_dates:
            logger.warning(f"发现{len(invalid_dates)}个无效上市日期：{invalid_dates[:10]}...")
        else:
            logger.info("✅ 上市日期格式校验通过")
        
        # 校验3：股票名称非空
        cursor.execute("SELECT stock_code FROM a_share_basic WHERE stock_name IS NULL OR stock_name='';")
        empty_names = cursor.fetchall()
        if empty_names:
            logger.warning(f"发现{len(empty_names)}个空名称股票：{empty_names[:10]}...")
        else:
            logger.info("✅ 股票名称非空校验通过")
        
        logger.info("===== a_share_basic表校验完成 =====")
    except Exception as e:
        logger.error(f"校验失败：{e}", exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()

# ========== 6. 定时维护 ==========
def start_scheduled_maintain():
    """启动定时维护（每日同步+每周校验）"""
    # 初始化表结构
    init_a_share_basic_table()
    
    # 初始化调度器
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    logger.info("启动a_share_basic表定时维护调度器")
    
    # 任务1：每日6:00增量同步（非交易时段，降低接口风控）
    scheduler.add_job(
        func=sync_a_share_basic,
        trigger=CronTrigger(hour=6, minute=0, timezone="Asia/Shanghai"),
        id="sync_a_share_basic_daily",
        replace_existing=True
    )
    
    # 任务2：每周日8:00数据校验
    scheduler.add_job(
        func=validate_a_share_basic,
        trigger=CronTrigger(day_of_week=0, hour=8, minute=0, timezone="Asia/Shanghai"),
        id="validate_a_share_basic_weekly",
        replace_existing=True
    )
    
    # 打印任务列表
    logger.info("定时任务列表：")
    for job in scheduler.get_jobs():
        logger.info(f"- {job.id}：{job.trigger}")
    
    # 启动调度器
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("手动终止调度器")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"调度器异常：{e}", exc_info=True)
        scheduler.shutdown()

# ========== 主入口 ==========
if __name__ == "__main__":
    # 可选执行方式：
    # 1. 手动执行一次同步+校验
    init_a_share_basic_table()
    sync_a_share_basic()
    validate_a_share_basic()
    
    # 2. 启动定时维护（推荐长期运行）
    # start_scheduled_maintain()
