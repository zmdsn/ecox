"""
数据库会话和仓库管理
提供统一的数据库连接、会话管理和仓库模式
"""

from contextlib import contextmanager
from typing import Generator, Optional, Type, TypeVar, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# 导入配置
from .config import PG_CONFIG

# 引擎全局变量
_engine: Optional = None
_session_factory: Optional[sessionmaker] = None
Base = declarative_base()


T = TypeVar("T")


class DatabaseError(Exception):
    """数据库错误"""

    pass


class DatabaseSession:
    """数据库会话管理"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or PG_CONFIG
        self._engine = None
        self._session_factory = None

    def get_engine(self):
        """获取或创建数据库引擎"""
        if self._engine is None:
            # 构建 PostgreSQL 连接 URL
            db_url = (
                f"postgresql+psycopg2://{self.database_config['user']}:"
                f"{self.database_config['password']}@"
                f"{self.database_config['host']}:"
                f"{self.database_config.get('port', 5432)}/"
                f"{self.database_config['database']}"
            )

            # 连接池配置
            self._engine = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.database_config.get("echo", False),
            )

            # 创建会话工厂
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                expire_on_commit=False,
            )

        return self._engine

    @property
    def database_config(self):
        return PG_CONFIG

    def get_session(self):
        """获取新的数据库会话"""
        return self._session_factory()

    @contextmanager
    def session(self):
        """上下文管理器，自动处理事务和关闭"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all(self):
        """创建所有表结构"""
        from . import models

        Base.metadata.create_all(self._engine)

    def drop_all(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(self._engine)

    def dispose(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 全局数据库实例
db: Optional[DatabaseSession] = None


def init_db(database_url: Optional[str] = None):
    """初始化全局数据库实例"""
    global db
    if db is None:
        db = DatabaseSession(database_url)
        db.get_engine()  # 初始化引擎
    return db


def get_db() -> DatabaseSession:
    """获取全局数据库实例（单例模式）"""
    global db
    if db is None:
        init_db()
    return db


@contextmanager
def get_db_session():
    """获取数据库会话的上下文管理器"""
    database = get_db()
    # 直接使用 database.session() 作为上下文管理器
    # 但因为我们需要作为函数返回，所以需要特殊处理
    session = database.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def query_to_dict(query_result: List[T]) -> List[dict]:
    """将 SQLAlchemy 查询结果转换为字典列表"""
    return [{c.__dict__ for c in query_result} for c in query_result]


def bulk_insert(
    session,
    model: Type[T],
    items: List[dict],
    chunk_size: int = 100,
) -> int:
    """
    批量插入数据（优化性能）

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        items: 要插入的数据列表（字典格式）
        chunk_size: 每批次大小

    Returns:
        插入的记录数
    """
    total_inserted = 0
    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        session.bulk_insert_mappings(model.__table__, chunk)
        total_inserted += len(chunk)
        session.commit()
    return total_inserted


def bulk_update(
    session,
    model: Type[T],
    items: List[dict],
    key_columns: List[str],
    chunk_size: int = 100,
) -> int:
    """
    批量更新数据（使用 ON CONFLICT）

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        items: 要更新的数据列表
        key_columns: 用于判断是否存在的键列
        chunk_size: 每批次大小

    Returns:
        更新的记录数
    """
    from sqlalchemy.dialects.postgresql import insert

    total_updated = 0

    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]

        for item in chunk:
            # 构建更新语句 - 排除 key_columns
            update_columns = {k: v for k, v in item.items() if k not in key_columns}
            stmt = insert(model).values(**item)
            stmt = stmt.on_conflict_do_update(
                index_elements=key_columns,
                set_=update_columns
            )

            session.execute(stmt)

        session.commit()
        total_updated += len(chunk)

    return total_updated


class Transaction:
    """事务上下文管理器"""

    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()

    def begin_nested(self):
        """开始嵌套事务"""
        return self.session.begin_nested()

    def commit(self):
        """提交事务"""
        self.session.commit()
