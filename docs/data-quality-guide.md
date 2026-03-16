# 数据质量指南

本文档说明 Ecox 项目中的数据质量保障机制。

## 概述

Ecox 实现了多层数据质量保障体系：

1. **模型层验证** - SQLAlchemy 模型自动验证代码格式和数据类型
2. **懒加载机制** - 自动获取和缓存财务数据
3. **业务验证** - 多维度数据验证确保数据质量

## 股票代码格式

### 标准格式

所有股票代码在系统中存储为带交易所前缀的格式：

- `SH` + 6位数字 - 上海证券交易所
- `SZ` + 6位数字 - 深圳证券交易所
- `BJ` + 6位数字 - 北京证券交易所

示例：
- `SH600000` - 浦发银行
- `SZ000001` - 平安银行
- `BJ430047` - 诺思兰德

### 代码格式化

使用 `code_format()` 函数自动格式化代码：

```python
from ecox.utils import code_format

code_format('600000')  # -> 'SH600000'
code_format('SH600000')  # -> 'SH600000'
code_format('sh600000')  # -> 'SH600000'
```

## 懒加载服务

### 工作原理

懒加载服务自动处理数据的获取和缓存：

1. 检查内存缓存
2. 检查数据库
3. 从 akshare 下载（如果需要）
4. 存储到数据库并更新缓存

### 使用示例

```python
from ecox.services.financial_analysis_service import FinancialAnalysisService

service = FinancialAnalysisService()

# 自动懒加载 - 如果数据库没有数据，会自动下载
result = service.calculate_metrics(
    stock_code='601318',  # 可以不带前缀
    modules=None  # 分析所有模块
)
```

### 缓存策略

不同报告类型有不同的缓存过期时间：

- Q1/Q2/Q3: 120天
- Q4: 180天

数据过期后会自动从 akshare 重新获取。

## 数据验证

### 验证层级

1. **模型层** - SQLAlchemy @validates 装饰器
2. **业务层** - ModelValidator 类
3. **数据库层** - 约束和触发器（可选）

### 验证规则

#### 基础规则
- 股票代码格式正确
- 必填字段不能为空
- 数值字段类型正确

#### 业务规则
- 收入不能为负
- 净利润不应超过收入的10倍（异常检测）
- 资产负债率不应超过100%

#### 勾稽关系
- 营业利润和净利润符号应一致
- 毛利率应在合理范围内

### 使用验证器

```python
from ecox.validators import ProfitSheetValidator

validator = ProfitSheetValidator()
data = {
    'stock_code': 'SH600000',
    'report_date': '2025-12-31',
    'total_revenue': 1000000000,
    'net_profit': 100000000
}

issues = validator.validate(data)
for issue in issues:
    print(f"{issue.field}: {issue.message} ({issue.severity})")
```

## 数据迁移

### 迁移脚本

使用 `scripts/migrate_stock_data.py` 迁移现有数据：

```bash
# 模拟运行（推荐先运行）
uv run python scripts/migrate_stock_data.py --dry-run

# 创建备份并迁移
uv run python scripts/migrate_stock_data.py --backup /path/to/backup.sql
```

### 迁移阶段

1. **备份** - 创建数据库备份
2. **代码格式统一** - 更新所有股票代码为带前缀格式
3. **验证** - 检查数据质量

## 错误处理

### 自定义异常

```python
from ecox.exceptions import (
    StockCodeError,
    DataValidationError,
    ExternalDataSourceError
)

# 使用错误处理装饰器
from ecox.error_handling import handle_errors

@handle_errors(default_return=None, raise_on_error=False)
def risky_function():
    # 可能失败的代码
    pass
```

## 日志

### 配置日志

```python
from ecox.logging_config import setup_logging, get_logger

# 配置日志系统
setup_logging(
    log_level="INFO",
    log_dir="./logs",
    enable_console=True,
    enable_file=True
)

# 获取日志器
logger = get_logger(__name__)
logger.info("Application started")
```

### 日志位置

- 控制台 - 实时输出
- 文件 - `logs/ecox_YYYY-MM-DD.log`
- 轮转策略 - 10MB/文件，保留5个文件

## 最佳实践

1. **使用懒加载** - 让系统自动处理数据获取
2. **验证输入** - 使用验证器检查数据质量
3. **处理异常** - 捕获并适当处理自定义异常
4. **检查日志** - 定期查看日志文件排查问题

## 故障排查

### 问题：数据查询失败

**原因**：股票代码格式不匹配

**解决**：
```python
from ecox.utils import code_format
formatted_code = code_format('600000')  # 使用格式化后的代码
```

### 问题：缓存数据过期

**原因**：数据超过了缓存过期时间

**解决**：强制刷新
```python
service.calculate_metrics('601318', force_refresh=True)
```

### 问题：akshare 下载失败

**原因**：网络问题或 API 限制

**解决**：系统会自动重试，或稍后再试

## 相关文档

- [设计文档](/docs/plans/2026-03-16-data-quality-refactor-design.md)
- [实施计划](/docs/plans/2026-03-16-data-quality-implementation-plan.md)
