# 股票基础信息下载测试设计文档

**日期**: 2026-03-03
**状态**: 已批准
**作者**: Claude + 用户协作设计

---

## 1. 概述

### 1.1 背景
Ecox 系统已有 `src/ecox/data/shares.py` 模块实现股票基础信息下载功能。本测试旨在验证现有功能的正确性，确保数据采集流程可靠。

### 1.2 目标
- 测试完整的股票基础信息下载流程
- 验证数据库同步正确性
- 使用小范围测试（约10只股票）快速验证
- 通过事务回滚保护数据库环境

---

## 2. 测试范围

### 2.1 被测模块
- **文件**: `src/ecox/data/shares.py`
- **核心函数**:
  - `get_stock_basic_raw()` - 从 akshare 获取股票代码
  - `supplement_stock_detail()` - 补充行业和上市日期
  - `sync_a_share_basic()` - 同步到数据库

### 2.2 测试数据范围
- 小范围测试：约 10 只股票
- 选取策略：取前 N 只或指定股票代码

---

## 3. 测试架构

```
┌─────────────────────────────────────────────────────┐
│                pytest 测试框架                       │
│  ┌───────────────────────────────────────────────┐  │
│  │            test_shares_download.py            │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │  test_sync_limited_stocks()             │  │  │
│  │  │  - 测试10只股票的完整流程                │  │  │
│  │  │  - 验证数据正确写入                      │  │  │
│  │  │  - 事务回滚保护                          │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │  test_get_stock_basic_raw()             │  │  │
│  │  │  - 验证akshare API调用                  │  │  │
│  │  │  - 检查返回数据格式                      │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │  test_supplement_stock_detail()         │  │  │
│  │  │  - 验证详情补充逻辑                      │  │  │
│  │  │  - 检查行业/日期字段                     │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 4. 测试用例设计

### 4.1 场景 1: 小范围完整流程测试

```python
def test_sync_limited_stocks(db_session):
    """
    测试约10只股票的完整下载流程
    - 使用事务回滚保护数据库
    - 验证数据正确写入
    """
    # 1. 获取原始数据（限制数量）
    raw_df = get_stock_basic_raw()
    test_df = raw_df.head(10)

    # 2. 补充详情
    detailed_df = supplement_stock_detail(test_df)

    # 3. 同步到数据库
    result = sync_a_share_basic(df=detailed_df, session=db_session)

    # 4. 验证
    assert result['success'] > 0
    assert result['failed'] == 0

    # 5. 数据库验证
    for code in test_df['stock_code']:
        record = db_session.query(StockBasic).filter_by(stock_code=code).first()
        assert record is not None
        assert record.stock_name is not None
```

### 4.2 场景 2: 单元测试 - API 调用

```python
def test_get_stock_basic_raw():
    """验证 akshare API 调用和数据格式"""
    df = get_stock_basic_raw()

    # 验证返回类型
    assert isinstance(df, pd.DataFrame)

    # 验证必需列存在
    assert 'stock_code' in df.columns
    assert 'stock_name' in df.columns

    # 验证数据非空
    assert len(df) > 0
    assert df['stock_code'].notna().all()
```

### 4.3 场景 3: 单元测试 - 详情补充

```python
def test_supplement_stock_detail():
    """验证详情补充逻辑"""
    # 准备测试数据
    test_df = pd.DataFrame({
        'stock_code': ['000001', '000002'],
        'stock_name': ['平安银行', '万科A']
    })

    # 补充详情
    result = supplement_stock_detail(test_df)

    # 验证新列存在
    assert 'industry' in result.columns
    assert 'list_date' in result.columns

    # 验证数据已填充
    assert result['industry'].notna().sum() > 0
```

---

## 5. 执行方式

```bash
# 运行所有测试
pytest tests/data/test_shares_download.py -v

# 运行特定测试场景
pytest tests/data/test_shares_download.py::test_sync_limited_stocks -v

# 查看详细输出
pytest tests/data/test_shares_download.py -v -s
```

---

## 6. 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| akshare API 调用失败 | 记录错误，标记测试失败 |
| 数据库连接失败 | 跳过测试（requires good DB connection） |
| 数据格式异常 | 断言检查，报告具体字段 |
| 事务回滚失败 | 清理测试数据（DELETE WHERE stock_code IN ...） |

---

## 7. 预期结果

测试通过后应验证：
- ✅ 能成功从 akshare 获取股票代码
- ✅ 能补充行业和上市日期信息
- ✅ 数据能正确写入数据库
- ✅ 事务回滚后数据库无残留数据

---

## 8. 文件结构

```
tests/
└── data/
    ├── __init__.py
    └── test_shares_download.py    # 新建测试文件
```

---

## 9. 依赖说明

- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持（如需要）
- **现有模块**: `src/ecox/data/shares.py`
- **数据库**: PostgreSQL（需有测试连接）
