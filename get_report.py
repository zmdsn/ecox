import os
import warnings
warnings.filterwarnings("ignore")

import akshare as ak
import psycopg2
import psycopg2.extras
import pandas as pd
import time
from datetime import datetime
from psycopg2 import OperationalError, ProgrammingError

# ========== 配置项 ==========
# PostgreSQL连接配置
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "zmdsn",
    "password": "zmdsnsdmz",
    "database": "stock",
    "options": "-c client_encoding=utf8"
}

# 反爬间隔（单股票/单报表抓取间隔，避免IP封禁）
CALL_INTERVAL = 5  # 秒
# 要抓取的报告期类型（全部/年度/季度，可选：['年报', '中报', '季报', '半年报']）
REPORT_TYPES = ["年报", "季报"]

# ========== PostgreSQL基础操作函数 ==========
def get_pg_conn():
    """创建PostgreSQL连接（带重连）"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = False
        return conn
    except OperationalError as e:
        print(f"数据库连接失败：{e}，5秒后重试...")
        time.sleep(5)
        return get_pg_conn()

def create_finance_tables():
    """创建三大财务报表表结构（适配PostgreSQL，兼容字段类型）"""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # 1. 利润表（stock_profit_sheet）
    create_profit_sql = """
    CREATE TABLE IF NOT EXISTS stock_profit_sheet (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        report_date VARCHAR(20) NOT NULL,  -- 报告期（如2024-03-31）
        report_type VARCHAR(10) NOT NULL,  -- 报告类型（年报/季报）
        total_revenue NUMERIC(20,2),       -- 营业总收入
        operating_profit NUMERIC(20,2),    -- 营业利润
        net_profit NUMERIC(20,2),          -- 净利润(归属于母公司股东)
        basic_eps NUMERIC(10,4),           -- 基本每股收益
        diluted_eps NUMERIC(10,4),         -- 稀释每股收益
        create_time TIMESTAMP DEFAULT NOW(),
        CONSTRAINT idx_profit_code_date UNIQUE (stock_code, report_date)
    );
    COMMENT ON TABLE stock_profit_sheet IS 'A股利润表（按报告期）';
    COMMENT ON COLUMN stock_profit_sheet.total_revenue IS '营业总收入(元)';
    COMMENT ON COLUMN stock_profit_sheet.operating_profit IS '营业利润(元)';
    COMMENT ON COLUMN stock_profit_sheet.net_profit IS '净利润(归属于母公司股东)(元)';
    COMMENT ON COLUMN stock_profit_sheet.basic_eps IS '基本每股收益(元/股)';
    COMMENT ON COLUMN stock_profit_sheet.diluted_eps IS '稀释每股收益(元/股)';
    """
    
    # 2. 资产负债表（stock_balance_sheet）
    create_balance_sql = """
    CREATE TABLE IF NOT EXISTS stock_balance_sheet (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        report_date VARCHAR(20) NOT NULL,
        report_type VARCHAR(10) NOT NULL,
        total_assets NUMERIC(20,2),        -- 总资产
        total_liabilities NUMERIC(20,2),   -- 总负债
        owner_equity NUMERIC(20,2),        -- 股东权益合计
        fixed_assets NUMERIC(20,2),        -- 固定资产
        create_time TIMESTAMP DEFAULT NOW(),
        CONSTRAINT idx_balance_code_date UNIQUE (stock_code, report_date)
    );
    COMMENT ON TABLE stock_balance_sheet IS 'A股资产负债表（按报告期）';
    COMMENT ON COLUMN stock_balance_sheet.total_assets IS '总资产(元)';
    COMMENT ON COLUMN stock_balance_sheet.total_liabilities IS '总负债(元)';
    COMMENT ON COLUMN stock_balance_sheet.owner_equity IS '股东权益合计(元)';
    COMMENT ON COLUMN stock_balance_sheet.fixed_assets IS '固定资产(元)';
    """
    
    # 3. 现金流量表（stock_cash_flow_sheet）
    create_cashflow_sql = """
    CREATE TABLE IF NOT EXISTS stock_cash_flow_sheet (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        report_date VARCHAR(20) NOT NULL,
        report_type VARCHAR(10) NOT NULL,
        report_date_type VARCHAR(10) NOT NULL,
        operating_cash_flow NUMERIC(20,2), -- 经营活动产生的现金流量净额
        investing_cash_flow NUMERIC(20,2), -- 投资活动产生的现金流量净额
        financing_cash_flow NUMERIC(20,2), -- 筹资活动产生的现金流量净额
        net_cash_flow NUMERIC(20,2),       -- 现金及现金等价物净增加额
        create_time TIMESTAMP DEFAULT NOW(),
        CONSTRAINT idx_cashflow_code_date UNIQUE (stock_code, report_date)
    );
    COMMENT ON TABLE stock_cash_flow_sheet IS 'A股现金流量表（按报告期）';
    COMMENT ON COLUMN stock_cash_flow_sheet.operating_cash_flow IS '经营活动产生的现金流量净额(元)';
    COMMENT ON COLUMN stock_cash_flow_sheet.investing_cash_flow IS '投资活动产生的现金流量净额(元)';
    COMMENT ON COLUMN stock_cash_flow_sheet.financing_cash_flow IS '筹资活动产生的现金流量净额(元)';
    COMMENT ON COLUMN stock_cash_flow_sheet.net_cash_flow IS '现金及现金等价物净增加额(元)';
    """
    
    try:
        # 执行建表语句
        cursor.execute(create_profit_sql)
        cursor.execute(create_balance_sql)
        cursor.execute(create_cashflow_sql)
        conn.commit()
        print("三大财务报表表结构创建/验证成功")
    except ProgrammingError as e:
        conn.rollback()
        print(f"建表失败：{e}")
    finally:
        cursor.close()
        conn.close()


def get_all_a_share_codes(filter_delist: bool = True) -> pd.DataFrame:
    """
    获取所有A股股票代码+名称（从a_share_basic表读取）
    :param filter_delist: 是否过滤退市股票（True=仅返回未退市，False=返回全部）
    :return: DataFrame，包含字段：stock_code(股票代码)、stock_name(股票名称)、industry(行业)、list_date(上市日期)、delist_date(退市日期)
    """
    # 1. 构建查询SQL（按需过滤退市股票）
    if filter_delist:
        # 仅查询未退市股票（delist_date为NULL）
        query_sql = """
        SELECT stock_code, stock_name, industry, list_date, delist_date 
        FROM a_share_basic 
        WHERE delist_date IS NULL;
        """
    else:
        # 查询所有股票（含退市）
        query_sql = """
        SELECT stock_code, stock_name, industry, list_date, delist_date 
        FROM a_share_basic;
        """
    
    conn = None
    cursor = None
    try:
        # 2. 建立数据库连接并执行查询
        conn = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute(query_sql)
        
        # 3. 获取查询结果并转换为DataFrame
        # 获取字段名（从cursor.description中提取）
        columns = [desc[0] for desc in cursor.description]
        # 获取数据行
        rows = cursor.fetchall()
        # 转换为DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # 4. 数据清洗（保证数据有效性）
        df = df.dropna(subset=["stock_code", "stock_name"])  # 剔除代码/名称为空的记录
        df = df[df["stock_code"].str.match(r"^\d{6}$")]      # 仅保留6位数字代码
        df = df.drop_duplicates(subset=["stock_code"])       # 剔除重复代码
        return df

    except Exception as e:
        # 异常处理：回滚事务（查询操作实际无需回滚，但保留以兼容后续扩展）
        if conn:
            conn.rollback()
        raise  # 抛出异常，让上层处理
    finally:
        # 确保游标和连接关闭
        if cursor:
            cursor.close()
        if conn:
            conn.close()    

def clean_finance_data(df, stock_code, stock_name, report_type):
    """清洗财务报表数据，统一字段格式"""
    # 只做最小必要的数据清洗：保留原列、规范报告日期、保留NaN以便插入时映射为NULL
    # 如果不存在 REPORT_DATE，直接返回原始 df
    if "REPORT_DATE" in df.columns:
        # 将 REPORT_DATE 转为标准 YYYY-MM-DD 字符串（遇到 NaN 则保留）
        def _fmt(x):
            try:
                s = str(x)
                if len(s) == 8 and s.isdigit():
                    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
                return s
            except Exception:
                return x

        df = df.copy()
        df["REPORT_DATE"] = df["REPORT_DATE"].apply(_fmt)
    return df

def code_format(secucode: str):
    if not isinstance(secucode, str):
        secucode = str(secucode)
    secucode = secucode.strip()
    if not secucode:
        return secucode
    first = secucode[0].upper()
    # 如果已经带有交易所前缀，直接返回大写格式
    if first in ("S", "B") and len(secucode) > 1:
        return secucode.upper()
    if first in ("0", "2", "3"):
        return "SZ" + secucode
    if first in ("920"):
        return "BJ" + secucode
    if first in ("6", "9"):
        return "SH" + secucode
    # 默认尝试北交所前缀
    return "BJ" + secucode


def crawl_profit_sheet(stock_code, stock_name):
    """抓取单只股票利润表"""
    try:
        file_name = f"./src/data/profit_sheet_{stock_code[-6:]}_.csv"
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, dtype={'SECURITY_CODE': str})
            return "skeep"
        else:
        # akshare 接口通常会返回多个报告期的数据，一次请求即可
            df = ak.stock_profit_sheet_by_report_em(symbol=code_format(stock_code))
            df.to_csv(file_name, index=False)
            time.sleep(CALL_INTERVAL)

        if df is None or df.empty:
            return pd.DataFrame()
        df = clean_finance_data(df, stock_code, stock_name, None)
        # 保留并映射核心字段（如果缺失则抛出清晰的KeyError）
        df = df[["SECURITY_CODE", "SECURITY_NAME_ABBR", "REPORT_DATE", "REPORT_TYPE", 
                "REPORT_DATE_NAME", "OPERATE_INCOME", "OPERATE_PROFIT", "PARENT_NETPROFIT", 
                 "BASIC_EPS", "DILUTED_EPS"]]
        df.rename(columns={
            "SECURITY_CODE": "stock_code",
            "SECURITY_NAME_ABBR": "stock_name",
            "REPORT_DATE": "report_date",
            "REPORT_TYPE": "report_type",
            "REPORT_DATE_NAME": "report_date_type",
            "OPERATE_INCOME": "total_revenue",
            "OPERATE_PROFIT": "operating_profit",
            "PARENT_NETPROFIT": "net_profit",
            "BASIC_EPS": "basic_eps",
            "DILUTED_EPS": "diluted_eps"
        }, inplace=True)
        # 稍作延迟以降低请求速率
        return df
    except Exception as e:
        print(f"[{stock_code}] 利润表抓取失败：{e}")
        return pd.DataFrame()

def crawl_balance_sheet(stock_code, stock_name):
    """抓取单只股票资产负债表"""
    try:
        file_name = f"./src/data/balance_sheet_{stock_code}_.csv"
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, dtype={'SECURITY_CODE': str})
        else:
        # akshare 接口通常会返回多个报告期的数据，一次请求即可
            df = ak.stock_balance_sheet_by_report_em(symbol=code_format(stock_code))
            df.to_csv(file_name, index=False)
            time.sleep(CALL_INTERVAL)
        if df is None or df.empty:
            return pd.DataFrame()
        df = clean_finance_data(df, stock_code, stock_name, None)
        df = df[["SECURITY_CODE", "SECURITY_NAME_ABBR", "REPORT_DATE", "REPORT_TYPE", 
                 "TOTAL_ASSETS", "TOTAL_LIABILITIES", "TOTAL_EQUITY", "FIXED_ASSET"]]
        df.rename(columns={
            "SECURITY_CODE": "stock_code",
            "SECURITY_NAME_ABBR": "stock_name",
            "REPORT_DATE": "report_date",
            "REPORT_TYPE": "report_type",
            "TOTAL_ASSETS": "total_assets",
            "TOTAL_LIABILITIES": "total_liabilities",
            "TOTAL_EQUITY": "owner_equity",
            "FIXED_ASSET": "fixed_assets"
        }, inplace=True)
        return df
    except Exception as e:
        print(f"[{stock_code}] 资产负债表抓取失败：{e}")
        return pd.DataFrame()

def crawl_cash_flow_sheet(stock_code, stock_name):
    """抓取单只股票现金流量表"""
    try:
        file_name = f"./src/data/cash_sheet_{stock_code}_.csv"
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, dtype={'SECURITY_CODE': str})
        else:
        # akshare 接口通常会返回多个报告期的数据，一次请求即可
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=code_format(stock_code))
            df.to_csv(file_name, index=False)
            time.sleep(CALL_INTERVAL)

        if df is None or df.empty:
            return pd.DataFrame()
        df = clean_finance_data(df, stock_code, stock_name, None)
        df = df[["SECURITY_CODE", "SECURITY_NAME_ABBR", "REPORT_DATE", "REPORT_TYPE", 
                 "NETCASH_OPERATE", "NETCASH_INVEST", "NETCASH_FINANCE", "CCE_ADD"]]
        df.rename(columns={
            "SECURITY_CODE": "stock_code",
            "SECURITY_NAME_ABBR": "stock_name",
            "REPORT_DATE": "report_date",
            "REPORT_TYPE": "report_type",
            "NETCASH_OPERATE": "operating_cash_flow",
            "NETCASH_INVEST": "investing_cash_flow",
            "NETCASH_FINANCE": "financing_cash_flow",
            "CCE_ADD": "net_cash_flow"
        }, inplace=True)
        return df
    except Exception as e:
        print(f"[{stock_code}] 现金流量表抓取失败：{e} {stock_code}")
        return pd.DataFrame()


def batch_insert_to_pg(df, table_name):
    """批量插入财务数据到PostgreSQL（忽略重复）"""
    if df.empty:
        return 0
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # 生成插入SQL（动态适配字段）
    columns = df.columns.tolist()
    placeholders = ", ".join(["%s"] * len(columns))
    # 使用 ON CONFLICT 指定冲突列（stock_code, report_date），避免依赖约束名
    insert_sql = f"""
    INSERT INTO {table_name} ({", ".join(columns)})
    VALUES ({placeholders})
    ON CONFLICT (stock_code, report_date) DO NOTHING;
    """
    
    # 转换数据为元组列表（保留类型并把 NaN 转为 None）
    data_list = []
    for _, row in df.iterrows():
        row_tuple = []
        for val in row.values:
            # pandas / numpy NaN -> None
            try:
                if pd.isna(val):
                    row_tuple.append(None)
                else:
                    row_tuple.append(val)
            except Exception:
                row_tuple.append(val)
        data_list.append(tuple(row_tuple))
    
    try:
        # 批量插入（每100条一批）
        batch_size = 100
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i+batch_size]
            psycopg2.extras.execute_batch(cursor, insert_sql, batch)
        conn.commit()
        print(f"[{table_name}] 批量插入完成，处理 {len(data_list)} 条记录（冲突将被忽略）")
        return len(data_list)
    except Exception as e:
        conn.rollback()
        print(f"[{table_name}] 插入失败：{e}")
        return 0
    finally:
        cursor.close()
        conn.close()


def main():
    """主程序：抓取所有A股三大财务报表并写入PostgreSQL"""
    # 1. 初始化表结构
    create_finance_tables()
    
    # 2. 获取所有A股代码
    code_name_df = get_all_a_share_codes()
    if code_name_df.empty:
        print("未获取到股票代码，程序退出")
        return
    total_stocks = len(code_name_df)
    print(f"共获取 {total_stocks} 只A股，开始抓取三大财务报表...")
    
    # 3. 遍历股票抓取+插入
    success_count = 0
    for idx, row in code_name_df.iterrows():
        stock_code = row["stock_code"]
        stock_name = row["stock_name"]
        print(f"\n===== 进度 {idx+1}/{total_stocks}：{stock_code} {stock_name} =====")
        
        # 抓取三大报表
        profit_df = crawl_profit_sheet(stock_code, stock_name)
        if isinstance(profit_df, str) and profit_df == "skeep":
            continue
        balance_df = crawl_balance_sheet(stock_code, stock_name)
        cashflow_df = crawl_cash_flow_sheet(stock_code, stock_name)
        
        # 插入数据库
        batch_insert_to_pg(profit_df, "stock_profit_sheet")
        batch_insert_to_pg(balance_df, "stock_balance_sheet")
        batch_insert_to_pg(cashflow_df, "stock_cash_flow_sheet")
        
        success_count += 1
        # 每抓取10只股票，暂停30秒（降低反爬风险）
        if (idx+1) % 10 == 0:
            print(f"已抓取 {idx+1} 只股票，暂停3秒...")
            time.sleep(3)
    
    print(f"\n抓取完成：共处理 {success_count} 只股票，数据已写入PostgreSQL")

if __name__ == "__main__":
    main()
