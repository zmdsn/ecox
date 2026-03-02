# 数据验证与清洗模块设计文档

**日期**: 2026-03-02
**状态**: 已批准
**作者**: Claude + 用户协作设计

---

## 1. 概述

### 1.1 背景
当前 Ecox 系统的数据采集流程缺少数据质量验证机制，可能导致异常数据入库影响回测结果。本设计旨在建立独立的数据验证模块，在数据下载时实时清洗和验证。

### 1.2 目标
- 在数据采集阶段实时验证数据质量
- 自动清洗可修复的异常数据
- 记录无法修复的数据问题并告警
- 确保入库数据的可靠性和完整性

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────┐
│  数据源 (akshare)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DailyUpdate     │
│   Service       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│      DataValidator          │
│  ┌───────────────────────┐  │
│  │ PriceValidator        │  │
│  │ VolumeValidator       │  │
│  │ MissingDataChecker    │  │
│  └───────────────────────┘  │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│ 合格  │ │ 不合格   │
│ 数据  │ │ 数据     │
└───┬───┘ └────┬─────┘
    ▼          ▼
┌───────┐ ┌──────────┐
│ 入库  │ │ 告警日志 │
└───────┘ └──────────┘
```

### 2.2 目录结构

```
src/ecox/
├── validators/
│   ├── __init__.py
│   ├── base.py              # 验证器基类
│   ├── price_validator.py   # 价格验证器
│   ├── volume_validator.py  # 成交量验证器
│   ├── missing_checker.py   # 缺失数据检查器
│   └── result.py            # ValidationResult 数据类
├── models/
│   └── __init__.py          # 新增 DataAlert 模型
└── services/
    └── daily_update_service.py  # 集成验证器
```

---

## 3. 组件设计

### 3.1 核心数据类

```python
@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool               # 是否有效
    errors: List[str]            # 错误列表
    warnings: List[str]          # 警告列表
    cleaned_data: Optional[Dict] = None  # 清洗后的数据
    alert_level: str = "INFO"    # INFO/WARNING/ERROR
```

### 3.2 验证器基类

```python
class DataValidator(ABC):
    """数据验证器基类"""

    @abstractmethod
    def validate(self, data: Dict) -> ValidationResult:
        """验证单条数据"""
        pass

    def validate_batch(self, data_list: List[Dict]) -> List[ValidationResult]:
        """批量验证"""
        return [self.validate(d) for d in data_list]
```

### 3.3 专用验证器

#### 3.3.1 PriceValidator 价格验证器
- 检查价格非负
- 检查价格在合理范围内（0.01 - 10000）
- 检查 OHLC 逻辑关系（high >= low, close 在 [low, high] 内）
- 检查涨跌幅合理性（单日不超过 20%，ST 股票不超过 5%）

#### 3.3.2 VolumeValidator 成交量验证器
- 检查成交量非负
- 检查成交额非负
- 检查成交额与成交量的合理性（成交额 >= 成交量 * 最低价）

#### 3.3.3 MissingDataChecker 缺失数据检查器
- 检查交易日连续性
- 检测跳空缺口（价格突变超过阈值）
- 检查是否有停牌日数据

---

## 4. 数据流程

### 4.1 验证流程

```
1. 获取数据
   akshare.stock_zh_a_hist()
        │
        ▼
2. 数据格式转换
   DataFrame → Dict List
        │
        ▼
3. 批量验证 【新增】
   DataValidator.validate_batch()
        │
        ├─────────────────────┬─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ 有效数据 │          │ 可修复  │          │ 无效数据 │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ 入库    │          │ 清洗后  │          │ 记录告警│
   └─────────┘          │ 入库    │          │         │
                       └─────────┘          └─────────┘
```

### 4.2 DailyUpdateService 集成

```python
class DailyUpdateService:
    def __init__(self):
        self.stock_service = StockService()
        self.validator = CompositeValidator([
            PriceValidator(),
            VolumeValidator(),
            MissingDataChecker()
        ])

    def save_price_data(self, stock_code: str, data_list: List[Dict]):
        # 先验证
        results = self.validator.validate_batch(data_list)

        # 分类处理
        valid_data = []
        alerts = []

        for data, result in zip(data_list, results):
            if result.is_valid:
                valid_data.append(result.cleaned_data or data)
            else:
                alerts.append(self._create_alert(stock_code, data, result))

        # 保存有效数据
        if valid_data:
            self._save_to_db(stock_code, valid_data)

        # 记录告警
        if alerts:
            self._save_alerts(alerts)
```

---

## 5. 告警机制

### 5.1 告警级别

| 级别 | 触发条件 | 处理方式 |
|------|----------|----------|
| ERROR | 数据无效无法修复 | 记录日志、不入库、发送告警 |
| WARNING | 数据异常但可修复 | 记录警告、清洗后入库 |
| INFO | 数据质量提示 | 仅记录 |

### 5.2 DataAlert 模型

```python
class DataAlert(Base):
    """数据告警记录表"""
    __tablename__ = "data_alerts"

    id = Column(Integer, primary_key=True)
    alert_level = Column(String(10))      # ERROR/WARNING/INFO
    stock_code = Column(String(20), index=True)
    stock_name = Column(String(100))
    alert_type = Column(String(50), index=True)  # price_invalid/volume_zero/...
    alert_message = Column(Text)
    raw_data = Column(JSON)               # 原始数据
    trade_date = Column(Date, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
```

### 5.3 告警类型

| 告警类型 | 说明 |
|----------|------|
| PRICE_NEGATIVE | 价格为负 |
| PRICE_ZERO | 价格为零（非停牌） |
| PRICE_OHLC_INVALID | OHLC 逻辑关系错误 |
| CHANGE_RATE_EXCEED | 涨跌幅超限 |
| VOLUME_NEGATIVE | 成交量为负 |
| VOLUME_ZERO | 成交量为零（有价格） |
| MISSING_DATA | 缺失交易日数据 |
| GAP_DETECTED | 价格跳空缺口 |

---

## 6. 配置参数

```python
# src/ecox/config.py 新增

class ValidationConfig:
    """验证配置"""

    # 价格范围
    MIN_PRICE = 0.01
    MAX_PRICE = 10000

    # 涨跌幅限制（普通股）
    MAX_CHANGE_RATE = 20  # %
    MAX_CHANGE_RATE_ST = 5  # % (ST股票)

    # 跳空检测阈值
    GAP_THRESHOLD = 15  # %

    # 缺失数据阈值
    MAX_MISSING_DAYS = 3

    # 是否启用严格模式（严格模式下 WARNING 也会拒绝入库）
    STRICT_MODE = False
```

---

## 7. 测试计划

### 7.1 单元测试

```
tests/validators/
├── test_price_validator.py
├── test_volume_validator.py
├── test_missing_checker.py
└── test_composite_validator.py
```

### 7.2 测试用例

| 用例 | 输入 | 预期输出 |
|------|------|----------|
| 正常数据 | 正常OHLC数据 | is_valid=True |
| 价格为负 | close=-1 | ERROR, is_valid=False |
| 价格为零 | close=0, 非停牌 | WARNING, 清洗为None |
| OHLC错误 | high<low | ERROR, is_valid=False |
| 涨跌幅超限 | 涨幅25% | WARNING |
| 成交量为负 | volume=-100 | ERROR |
| 连续缺失 | 缺3天数据 | WARNING |

### 7.3 集成测试

- 模拟 akshare 异常响应，验证完整流程
- 验证告警记录正确写入数据库
- 验证清洗后的数据正确入库

---

## 8. 实施步骤

1. **阶段一：基础框架** (1-2天)
   - 创建 validators 目录结构
   - 实现 ValidationResult 数据类
   - 实现 DataValidator 基类

2. **阶段二：验证器实现** (2-3天)
   - 实现 PriceValidator
   - 实现 VolumeValidator
   - 实现 MissingDataChecker
   - 实现 CompositeValidator

3. **阶段三：告警系统** (1-2天)
   - 创建 DataAlert 模型
   - 实现告警记录逻辑
   - 编写数据库迁移脚本

4. **阶段四：服务集成** (1天)
   - 修改 DailyUpdateService
   - 集成验证器流程

5. **阶段五：测试** (1-2天)
   - 编写单元测试
   - 编写集成测试
   - 测试覆盖率 > 80%

---

## 9. 扩展性考虑

### 9.1 未来可扩展功能

- 自定义验证规则配置
- 验证器插件机制
- 机器学习异常检测
- 实时数据大屏监控
- 钉钉/企业微信告警集成

### 9.2 性能考虑

- 批量验证减少数据库往返
- 异步告警发送
- 告警数据定期归档
