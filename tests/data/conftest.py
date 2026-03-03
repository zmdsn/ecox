"""pytest fixtures for data module tests"""
import pytest
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function")
def db_session():
    """
    数据库会话 fixture（带事务回滚）
    测试结束后自动回滚，保护数据库

    注意：使用嵌套事务（SAVEPOINT）来避免与 get_db_session 的
    事务管理冲突，确保测试数据完全隔离。
    """
    from src.ecox.database import get_db_session

    with get_db_session() as session:
        # 使用嵌套事务（SAVEPOINT）实现测试隔离
        # 这样不会与 get_db_session 的事务管理冲突
        nested = session.begin_nested()

        yield session

        # 回滚嵌套事务，撤销测试中的所有数据库更改
        nested.rollback()
        # 确保外层事务也回滚（因为 get_db_session 会在异常时回滚）
        session.rollback()


@pytest.fixture(scope="function")
def sample_stock_codes():
    """小范围测试用的股票代码（10只）"""
    return ["000001", "000002", "000004", "000005", "000006",
            "000007", "000008", "000009", "000010", "000011"]
