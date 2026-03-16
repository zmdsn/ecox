# Ecox 数据质量重构设计文档

**日期**: 2026-03-16
**作者**: Claude
**版本**: 1.0
**状态**: 待实施

---

## 1. 项目背景

### 1.1 现状分析

在财务分析过程中发现了以下数据质量问题：

1. **股票代码格式不一致**
   - `code_format()` 函数会添加交易所前缀（SH/SZ/BJ）
   - 数据库中存储的代码不带前缀
   - 导致查询失败，需要手动处理格式转换

2. **财务数据不完整**
   - `extra_data` 字段为空，缺少完整的原始财报数据
   - 仅有少量核心字段，无法支持深度分析

3. **缺少数据验证机制**
   - 入库数据缺少验证
   - 可能存在异常值或错误数据

4. **用户体验不佳**
   - 需要手动下载财报数据
   - 数据更新不及时

### 1.2 改进目标

1. **统一数据格式** - 在模型层自动处理代码格式
2. **补充完整数据** - 自动获取和存储完整财报原始数据
3. **建立验证机制** - 多层数据验证确保数据质量
4. **优化用户体验** - 懒加载模式自动获取数据

---

## 2. 整体架构设计

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Services)                     │
│  - FinancialAnalysisService                            │
│  - LazyLoadingService (新增)                           │
│  - FinancialReportService                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 数据模型层 (Models)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  BaseMixin (新增)                                │   │
│  │  - 标准化代码格式                               │   │
│  │  - 数据验证钩子                                 │   │
│  │  - 自动填充 extra_data                           │   │
│  └─────────────────────────────────────────────────┘   │
│           ▲            ▲            ▲                    │
│           │            │            │                    │
│  ┌────────┴────┐ ┌────┴─────┐ ┌──┴──────────┐         │
│  │StockProfit  │ │Stock     │ │Stock Cash   │         │
│  │Sheet        │ │Balance   │ │Flow Sheet   │         │
│  └─────────────┘ └──────────┘ └─────────────┘         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              数据库层 (PostgreSQL)                       │
│  - 统一的代码格式（SH/SZ前缀）                           │
│  - 完整的 extra_data JSON 字段                          │
│  - 数据约束和触发器（可选）                              │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心改进

1. **BaseMixin 基类** - 所有财务报表模型继承，提供统一功能
2. **LazyLoadingService** - 懒加载服务，自动获取和缓存数据
3. **ModelValidator** - 数据验证器，确保数据质量
4. **统一异常处理** - 完善的错误处理和日志系统

---

## 3. 数据模型层改进

### 3.1 文件结构

```
src/ecox/
├── models/
│   ├── __init__.py
│   ├── base.py              # 新增：BaseMixin 和基类
│   ├── stock_profit_sheet.py
│   ├── stock_balance_sheet.py
│   └── stock_cash_flow_sheet.py
├── validators/
│   └── model_validators.py  # 新增：模型层验证器
└── utils/
    └── code_format.py        # 改进：增强的代码格式化
```

### 3.2 BaseMixin 设计

```python
# src/ecox/models/base.py

from sqlalchemy import event
from sqlalchemy.orm import declared_attr, validates
from ..utils import code_format

class BaseMixin:
    """所有财务报表模型的混合基类"""

    @declared_attr
    def stock_code(cls):
        return Column(String(10), nullable=False, index=True)

    @property
    def formatted_code(self):
        """获取格式化的代码（带前缀）"""
        return code_format(self.stock_code)

    @formatted_code.setter
    def stock_code(self, value):
        """设置代码时自动格式化"""
        self._stock_code = code_format(value)

    def ensure_extra_data(self, raw_data: dict):
        """确保 extra_data 包含完整的原始数据"""
        if not self.extra_data:
            self.extra_data = raw_data
        else:
            for key, value in raw_data.items():
                if key not in self.extra_data:
                    self.extra_data[key] = value

    @validates('stock_code')
    def validate_stock_code(self, key, value):
        """验证股票代码格式"""
        formatted = code_format(value)
        if not self._is_valid_code(formatted):
            raise ValueError(f"Invalid stock code format: {value}")
        return formatted

    def _is_valid_code(self, code: str) -> bool:
        """检查代码是否有效"""
        import re
        return bool(re.match(r'^(SH|SZ|BJ)\d{6}$', code))
```

### 3.3 模型示例

```python
# src/ecox/models/stock_profit_sheet.py

from sqlalchemy import Column, String, Numeric, DateTime, JSON
from .base import BaseMixin

class StockProfitSheet(Base, BaseMixin):
    __tablename__ = 'stock_profit_sheet'

    # 继承自 BaseMixin: stock_code（自动格式化）

    stock_name = Column(String(50))
    report_date = Column(DateTime, nullable=False, index=True)
    report_type = Column(String(20))

    # 核心字段
    total_revenue = Column(Numeric(30, 2))
    operating_profit = Column(Numeric(30, 2))
    net_profit = Column(Numeric(30, 2))
    basic_eps = Column(Numeric(10, 2))

    # 完整原始数据
    extra_data = Column(JSON)

    # 数据验证
    @validates('total_revenue', 'operating_profit', 'net_profit')
    def validate_positive_numbers(self, key, value):
        """验证金额字段"""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative: {value}")
        return value
```

---

## 4. 数据验证机制

### 4.1 多层验证体系

```
Layer 1: SQLAlchemy Validators (模型层)
  - @validates 装饰器
  - 字段类型、格式、范围验证

Layer 2: Business Validators (业务层)
  - ModelValidator 类
  - 勾稽关系检查、逻辑一致性

Layer 3: Database Constraints (数据库层)
  - CHECK 约束
  - UNIQUE 约束
  - NOT NULL 约束
```

### 4.2 ModelValidator 设计

```python
# src/ecox/validators/model_validators.py

from dataclasses import dataclass
from enum import Enum

class ValidationSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None

class ModelValidator:
    """模型验证器基类"""

    def validate(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        issues.extend(self._validate_required_fields(data))
        issues.extend(self._validate_types(data))
        issues.extend(self._validate_business_rules(data))
        issues.extend(self._validate_cross_field_relations(data))
        return issues

    def _validate_business_rules(self, data: Dict) -> List[ValidationIssue]:
        issues = []

        # 收入不能为负
        if data.get('total_revenue', 0) < 0:
            issues.append(ValidationIssue(
                field='total_revenue',
                message="Revenue cannot be negative",
                severity=ValidationSeverity.ERROR
            ))

        # 异常检测：净利润不应超过营收的10倍
        revenue = data.get('total_revenue', 0)
        profit = data.get('net_profit', 0)
        if revenue > 0 and abs(profit) > abs(revenue) * 10:
            issues.append(ValidationIssue(
                field='net_profit',
                message="Net profit anomaly: exceeds 10x revenue",
                severity=ValidationSeverity.WARNING
            ))

        return issues
```

---

## 5. 懒加载机制

### 5.1 工作流程

```
用户请求
  │
  ▼
检查缓存 (内存)
  │ 命中？────是──► 返回缓存数据
  │否
  ▼
检查数据库
  │ 命中？────是──► 检查过期？────否──► 更新缓存 ─► 返回
  │否            │是
  │              └──► 过期，继续
  ▼
调用 akshare 下载
  │
  ▼
数据验证
  │
  ▼
存入数据库 + 更新缓存
  │
  └──► 返回数据
```

### 5.2 LazyLoadingService 核心功能

```python
class LazyLoadingService:
    """懒加载服务"""

    CACHE_EXPIRY_DAYS = {
        'Q1': 120,    # 一季报：4个月后过期
        'Q2': 120,    # 中报：4个月后过期
        'Q3': 120,    # 三季报：4个月后过期
        'Q4': 180,    # 年报：6个月后过期
    }

    @lru_cache(maxsize=128)
    def get_financial_data(
        self,
        stock_code: str,
        report_date: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """获取财务数据（懒加载模式）"""
        # 1. 检查内存缓存
        # 2. 检查数据库
        # 3. 从 akshare 下载
        # 4. 存储并缓存
        pass

    def _fetch_from_akshare(self, stock_code: str):
        """从 akshare 获取数据（带并发控制）"""
        # 防止重复下载
        # 并行下载三大报表
        pass
```

### 5.3 使用示例

```python
from ecox.services.financial_analysis_service import FinancialAnalysisService

service = FinancialAnalysisService()

# 自动懒加载：如果数据库没有，会自动下载
result = service.calculate_metrics(
    stock_code='601318',  # 可以不带前缀
    report_date=None,     # 自动获取最新
    modules=None,         # 分析所有模块
)

# 强制刷新数据
result = service.calculate_metrics(
    stock_code='601318',
    force_refresh=True    # 强制从 akshare 重新下载
)
```

---

## 6. 数据迁移策略

### 6.1 迁移阶段

```
Phase 1: 备份与评估 (1-2天)
  - 备份现有数据库
  - 评估数据质量和迁移范围

Phase 2: 代码格式统一 (2-3天)
  - 更新所有股票代码为带前缀格式
  - 批量验证代码格式

Phase 3: 补充 extra_data (3-5天)
  - 从 akshare 重新获取完整财报数据
  - 填充 extra_data 字段
  - 数据验证和清洗

Phase 4: 部署与验证 (1-2天)
  - 部署新的模型层代码
  - 运行完整验证测试
  - 灰度发布
```

### 6.2 迁移脚本

```python
# scripts/migrate_stock_data.py

class DataMigrator:
    """数据迁移器"""

    def backup_database(self, backup_path: str):
        """备份数据库"""
        pass

    def migrate_stock_codes(self) -> Dict[str, int]:
        """迁移股票代码格式"""
        pass

    def fetch_and_populate_extra_data(self, stock_code: str) -> bool:
        """从 akshare 获取并填充 extra_data"""
        pass

    def validate_migrated_data(self) -> List[Dict]:
        """验证迁移后的数据"""
        pass

    def run_full_migration(self):
        """执行完整迁移流程"""
        # Phase 1: 备份
        # Phase 2: 代码格式统一
        # Phase 3: 补充 extra_data
        # Phase 4: 验证
        pass
```

### 6.3 回滚机制

```python
class RollbackManager:
    """迁移回滚管理器"""

    def rollback(self):
        """回滚到迁移前状态"""
        # 恢复数据库备份
        pass
```

---

## 7. 错误处理和日志

### 7.1 自定义异常

```python
# src/ecox/exceptions.py

class EcoxException(Exception):
    """Ecox 基础异常类"""
    pass

class StockCodeError(EcoxException):
    """股票代码格式错误"""
    pass

class DataValidationError(EcoxException):
    """数据验证错误"""
    pass

class DataIntegrityError(EcoxException):
    """数据完整性错误"""
    pass

class MigrationError(EcoxException):
    """数据迁移错误"""
    pass

class ExternalDataSourceError(EcoxException):
    """外部数据源错误"""
    pass
```

### 7.2 错误处理装饰器

```python
# src/ecox/utils/error_handling.py

def handle_errors(
    default_return: Any = None,
    raise_on_error: bool = False,
    log_level: str = "ERROR"
):
    """错误处理装饰器"""
    pass

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """重试装饰器（用于外部数据源调用）"""
    pass
```

### 7.3 统一日志配置

```python
# src/ecox/logging_config.py

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    enable_console: bool = True,
    enable_file: bool = True
):
    """配置统一日志系统"""
    # 控制台输出
    # 文件轮转（10MB，保留5个）
    # 第三方库日志级别控制
    pass
```

---

## 8. 实施计划

### 8.1 优先级

| 任务 | 优先级 | 预计时间 |
|------|--------|----------|
| BaseMixin 基类实现 | P0 | 2天 |
| 股票代码格式统一 | P0 | 2天 |
| 懒加载服务实现 | P0 | 3天 |
| 数据验证器实现 | P1 | 3天 |
| 补充 extra_data | P1 | 5天 |
| 错误处理和日志 | P1 | 2天 |
| 数据迁移脚本 | P2 | 3天 |
| 测试和验证 | P2 | 3天 |

### 8.2 风险控制

1. **数据备份** - 迁移前必须完整备份数据库
2. **灰度发布** - 先在小范围测试，再全面推广
3. **回滚准备** - 准备完整的回滚方案
4. **监控告警** - 实时监控数据质量和系统性能

### 8.3 成功标准

1. ✅ 所有股票代码格式统一（带前缀）
2. ✅ extra_data 字段填充率 > 95%
3. ✅ 数据验证通过率 > 99%
4. ✅ 懒加载成功率 > 98%
5. ✅ 用户体验明显改善（无需手动下载数据）

---

## 9. 附录

### 9.1 相关文件

- 设计文档: `docs/plans/2026-03-16-data-quality-refactor-design.md`
- 迁移脚本: `scripts/migrate_stock_data.py`
- 模型定义: `src/ecox/models/base.py`
- 验证器: `src/ecox/validators/model_validators.py`
- 懒加载服务: `src/ecox/services/lazy_loading_service.py`

### 9.2 参考资料

- SQLAlchemy 文档: https://docs.sqlalchemy.org/
- Akshare 文档: https://akshare.akfamily.xyz/
- Python 数据验证最佳实践

---

**文档版本**: 1.0
**最后更新**: 2026-03-16
**状态**: 待实施
