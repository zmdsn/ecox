# 股票基础信息下载测试实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `src/ecox/data/shares.py` 模块创建 pytest 测试，验证股票基础信息下载功能的正确性。

**Architecture:** 使用 pytest 框架创建独立测试文件，通过事务回滚保护数据库，小范围测试（10只股票）快速验证现有功能。

**Tech Stack:** pytest, pytest-cov, SQLAlchemy ORM, akshare (被测依赖)

---

## Task 1: 创建测试目录结构和 conftest.py

**Files:**
- Create: `tests/data/__init__.py`
- Create: `tests/data/conftest.py`

**Step 1: 创建 tests/data/__init__.py**

```python
# tests/data/__init__.py
"""数据模块测试"""
```

**Step 2: 创建 tests/data/conftest.py（测试 fixtures）**

```python
# tests/data/conftest.py
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
    """
    from src.ecox.database import get_db_session

    with get_db_session() as session:
        # 开始事务
        connection = session.connection()
        transaction = connection.begin()

        yield session

        # 回滚事务
        session.rollback()
        transaction.rollback()


@pytest.fixture(scope="function")
def sample_stock_codes():
    """小范围测试用的股票代码（10只）"""
    return ["000001", "000002", "000004", "000005", "000006",
            "000007", "000008", "000009", "000010", "000011"]
```

**Step 3: 提交**

```bash
git add tests/data/__init__.py tests/data/conftest.py
git commit -m "test: 创建测试目录结构和 fixtures"
```

---

## Task 2: 编写 get_stock_basic_raw() 单元测试

**Files:**
- Create: `tests/data/test_shares_download.py`

**Step 1: 编写测试函数**

```python
# tests/data/test_shares_download.py
"""
测试股票基础信息下载功能
测试模块: src/ecox/data/shares.py
"""
import pytest
import pandas as pd
from src.ecox.data.shares import get_stock_basic_raw


class TestGetStockBasicRaw:
    """测试 get_stock_basic_raw() 函数"""

    def test_returns_dataframe(self):
        """验证返回类型为 DataFrame"""
        df = get_stock_basic_raw()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """验证必需列存在"""
        df = get_stock_basic_raw()
        required_columns = ["stock_code", "stock_name"]
        for col in required_columns:
            assert col in df.columns, f"缺少列: {col}"

    def test_data_not_empty(self):
        """验证数据非空"""
        df = get_stock_basic_raw()
        assert len(df) > 0, "返回数据为空"

    def test_stock_code_format(self):
        """验证股票代码格式（6位数字）"""
        df = get_stock_basic_raw()
        # 所有代码应该是6位数字
        assert df["stock_code"].str.match(r"^\d{6}$").all(), "股票代码格式错误"

    def test_no_duplicates(self):
        """验证无重复代码"""
        df = get_stock_basic_raw()
        duplicate_count = df["stock_code"].duplicated().sum()
        assert duplicate_count == 0, f"存在 {duplicate_count} 个重复代码"
```

**Step 2: 运行测试验证通过**

```bash
# cd 到项目根目录
cd /home/zmdsn/ecox

# 运行测试
uv run pytest tests/data/test_shares_download.py::TestGetStockBasicRaw -v
```

预期输出:
```
collected 5 items

test_shares_download.py::TestGetStockBasicRaw::test_returns_dataframe PASSED
test_shares_download.py::TestGetStockBasicRaw::test_has_required_columns PASSED
test_shares_download.py::TestGetStockBasicRaw::test_data_not_empty PASSED
test_shares_download.py::TestGetStockBasicRaw::test_stock_code_format PASSED
test_shares_download.py::TestGetStockBasicRaw::test_no_duplicates PASSED
```

**Step 3: 提交**

```bash
git add tests/data/test_shares_download.py
git commit -m "test: 添加 get_stock_basic_raw() 单元测试"
```

---

## Task 3: 编写 supplement_stock_detail() 单元测试

**Files:**
- Modify: `tests/data/test_shares_download.py`

**Step 1: 在文件中添加新的测试类**

```python
# 在 tests/data/test_shares_download.py 末尾添加

from src.ecox.data.shares import supplement_stock_detail


class TestSupplementStockDetail:
    """测试 supplement_stock_detail() 函数"""

    def test_supplements_industry_column(self):
        """验证补充 industry 列"""
        # 准备测试数据（2只股票，减少 API 调用）
        test_df = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "stock_name": ["平安银行", "万科A"]
        })

        result = supplement_stock_detail(test_df)

        # 验证新列存在
        assert "industry" in result.columns
        assert "list_date" in result.columns
        assert "delist_date" in result.columns

    def test_preserves_original_data(self):
        """验证保留原始数据"""
        test_df = pd.DataFrame({
            "stock_code": ["000001"],
            "stock_name": ["平安银行"]
        })

        result = supplement_stock_detail(test_df)

        # 验证原始数据未丢失
        assert result["stock_code"].iloc[0] == "000001"
        assert result["stock_name"].iloc[0] == "平安银行"

    def test_has_industry_data(self):
        """验证行业数据被填充"""
        test_df = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "stock_name": ["平安银行", "万科A"]
        })

        result = supplement_stock_detail(test_df)

        # 至少有一只股票获取到行业信息
        valid_industries = result["industry"].notna().sum()
        assert valid_industries > 0, "未获取到任何行业信息"
```

**Step 2: 运行测试验证通过**

```bash
uv run pytest tests/data/test_shares_download.py::TestSupplementStockDetail -v
```

预期输出:
```
collected 3 items

test_shares_download.py::TestSupplementStockDetail::test_supplements_industry_column PASSED
test_shares_download.py::TestSupplementStockDetail::test_preserves_original_data PASSED
test_shares_download.py::TestSupplementStockDetail::test_has_industry_data PASSED
```

**Step 3: 提交**

```bash
git add tests/data/test_shares_download.py
git commit -m "test: 添加 supplement_stock_detail() 单元测试"
```

---

## Task 4: 编写数据库同步集成测试

**Files:**
- Modify: `tests/data/test_shares_download.py`

**Step 1: 添加数据库同步测试类**

```python
# 在 tests/data/test_shares_download.py 末尾添加

from src.ecox.services import StockService
from src.ecox.models import StockBasic


class TestDatabaseSync:
    """测试数据库同步功能"""

    def test_sync_limited_stocks(self, db_session):
        """
        测试小范围股票同步（完整流程）
        使用事务回滚保护数据库
        """
        # 获取原始数据并限制为10只
        from src.ecox.data.shares import get_stock_basic_raw, supplement_stock_detail

        raw_df = get_stock_basic_raw()
        test_df = raw_df.head(10).copy()

        # 补充详情
        detailed_df = supplement_stock_detail(test_df)

        # 同步到数据库
        stock_service = StockService()
        success_count = 0

        for _, row in detailed_df.iterrows():
            try:
                stock_service.save_stock_info(
                    stock_code=row["stock_code"],
                    stock_name=row["stock_name"],
                    list_date=row.get("list_date"),
                    session=db_session
                )
                success_count += 1
            except Exception as e:
                print(f"同步 {row['stock_code']} 失败: {e}")

        # 验证成功数量
        assert success_count >= 5, f"成功同步数量过低: {success_count}/10"

        # 验证数据库中的记录
        for code in test_df["stock_code"].head(5):
            record = db_session.query(StockBasic).filter_by(stock_code=code).first()
            assert record is not None, f"股票 {code} 未找到"
            assert record.stock_name is not None, f"股票 {code} 名称为空"

    def test_update_existing_stock(self, db_session):
        """测试更新已存在的股票"""
        stock_service = StockService()

        # 先插入一条记录
        stock_service.save_stock_info(
            stock_code="999999",
            stock_name="测试股票",
            list_date=None,
            session=db_session
        )

        # 验证插入成功
        record = db_session.query(StockBasic).filter_by(stock_code="999999").first()
        assert record.stock_name == "测试股票"

        # 更新记录
        stock_service.save_stock_info(
            stock_code="999999",
            stock_name="更新后的测试股票",
            list_date=None,
            session=db_session
        )

        # 验证更新成功（需要刷新或重新查询）
        db_session.refresh(record)
        assert record.stock_name == "更新后的测试股票"
```

**Step 2: 运行测试验证通过**

```bash
uv run pytest tests/data/test_shares_download.py::TestDatabaseSync -v -s
```

预期输出:
```
collected 2 items

test_shares_download.py::TestDatabaseSync::test_sync_limited_stocks PASSED
test_shares_download.py::TestDatabaseSync::test_update_existing_stock PASSED
```

**Step 3: 提交**

```bash
git add tests/data/test_shares_download.py
git commit -m "test: 添加数据库同步集成测试"
```

---

## Task 5: 运行全部测试并生成覆盖率报告

**Files:**
- None（运行现有测试）

**Step 1: 运行全部测试**

```bash
# 运行所有测试
uv run pytest tests/data/test_shares_download.py -v
```

预期输出:
```
collected 10 items

test_shares_download.py::TestGetStockBasicRaw::test_returns_dataframe PASSED
test_shares_download.py::TestGetStockBasicRaw::test_has_required_columns PASSED
test_shares_download.py::TestGetStockBasicRaw::test_data_not_empty PASSED
test_shares_download.py::TestGetStockBasicRaw::test_stock_code_format PASSED
test_shares_download.py::TestGetStockBasicRaw::test_no_duplicates PASSED
test_shares_download.py::TestSupplementStockDetail::test_supplements_industry_column PASSED
test_shares_download.py::TestSupplementStockDetail::test_preserves_original_data PASSED
test_shares_download.py::TestSupplementStockDetail::test_has_industry_data PASSED
test_shares_download.py::TestDatabaseSync::test_sync_limited_stocks PASSED
test_shares_download.py::TestDatabaseSync::test_update_existing_stock PASSED
```

**Step 2: 生成覆盖率报告**

```bash
# 如果没有安装 pytest-cov，先安装
uv add --dev pytest-cov

# 生成覆盖率报告
uv run pytest tests/data/test_shares_download.py --cov=src/ecox/data/shares --cov-report=term-missing
```

**Step 3: 提交**

```bash
git add pyproject.toml  # 如果修改了依赖
git commit -m "test: 完成测试套件，添加 pytest-cov 依赖"
```

---

## Task 6: 验证数据库无残留数据

**Files:**
- None（验证步骤）

**Step 1: 查询数据库验证测试后无残留**

```bash
# 连接数据库查询测试用的股票代码是否被清理
uv run python -c "
from src.ecox.database import get_db_session
from src.ecox.models import StockBasic

with get_db_session() as session:
    # 检查测试用的 999999 代码（应该不存在）
    test_record = session.query(StockBasic).filter_by(stock_code='999999').first()
    if test_record:
        print('WARNING: 测试数据未清理，发现残留记录')
    else:
        print('OK: 测试数据已清理，无残留记录')

    # 检查前10只股票（测试前应已存在）
    first_10 = session.query(StockBasic).limit(10).all()
    print(f'数据库中前10条记录: {[s.stock_code for s in first_10]}')
"
```

预期输出:
```
OK: 测试数据已清理，无残留记录
数据库中前10条记录: ['000001', '000002', ...]
```

**Step 2: 提交（如需添加清理脚本）**

如果有清理脚本则提交，否则跳过。

---

## 运行完整测试套件

```bash
# 运行所有测试
uv run pytest tests/data/ -v

# 带覆盖率
uv run pytest tests/data/ --cov=src/ecox/data/shares --cov-report=html

# 查看详细输出
uv run pytest tests/data/ -v -s
```

## 验证清单

- [ ] Task 1: 测试目录和 fixtures 创建完成
- [ ] Task 2: get_stock_basic_raw() 测试通过
- [ ] Task 3: supplement_stock_detail() 测试通过
- [ ] Task 4: 数据库同步测试通过
- [ ] Task 5: 全部测试通过，覆盖率报告生成
- [ ] Task 6: 数据库无测试残留数据
