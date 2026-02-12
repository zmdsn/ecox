"""
数据库连接模块
提供统一的数据库连接函数，避免代码重复
"""

import logging
import time

import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError

from .config import PG_CONFIG

logger = logging.getLogger(__name__)


def get_connection():
    """
    创建PostgreSQL连接（基础版本）

    Returns:
        psycopg2.connection: 数据库连接对象
    """
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = False
        return conn
    except OperationalError as e:
        logger.error(f"数据库连接失败：{e}")
        raise


def get_connection_with_retry(max_retries: int = 3, retry_delay: int = 5):
    """
    创建PostgreSQL连接（带重试机制）

    Args:
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试间隔（秒），默认5秒

    Returns:
        psycopg2.connection: 数据库连接对象

    Raises:
        Exception: 多次重试后仍然失败
    """
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            conn.autocommit = False
            logger.info("数据库连接成功")
            return conn
        except OperationalError as e:
            retry_count += 1
            last_error = e
            logger.warning(f"数据库连接失败（重试{retry_count}/{max_retries}）：{e}")
            if retry_count < max_retries:
                time.sleep(retry_delay)

    raise Exception(f"数据库多次连接失败，终止任务。最后错误: {last_error}")


def get_connection_with_recursive_retry(retry_delay: int = 5):
    """
    创建PostgreSQL连接（递归重试版本，兼容旧代码）

    Args:
        retry_delay: 重试间隔（秒），默认5秒

    Returns:
        psycopg2.connection: 数据库连接对象
    """
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = False
        return conn
    except OperationalError as e:
        logger.warning(f"数据库连接失败：{e}，{retry_delay}秒后重试...")
        time.sleep(retry_delay)
        return get_connection_with_recursive_retry(retry_delay)


def get_dict_cursor(connection=None):
    """
    获取字典游标（返回字典格式的查询结果）

    Args:
        connection: 数据库连接，如果为None则创建新连接

    Returns:
        tuple: (connection, cursor) 元组
    """
    if connection is None:
        connection = get_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return connection, cursor


# 向后兼容的别名
get_pg_conn = get_connection_with_retry
get_pg_connection = get_connection_with_recursive_retry
