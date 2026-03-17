# Ecox AI 智能体系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 构建一个全功能的 A 股投资智能体系统，支持多轮对话、工具调用，并提供与 OpenAI API 兼容的接口

**架构:** LiteLLM API 服务器 + 自定义 Agent 层 + Ecox 服务层，通过 FastAPI 提供 OpenAI 兼容的 /v1/chat/completions 端点

**技术栈:** Python 3.13, FastAPI, LiteLLM, SQLAlchemy, PostgreSQL, httpx

---

## Task 1: 创建 Agent 模块目录结构

**Files:**
- Create: `src/ecox/agent/__init__.py`
- Create: `src/ecox/agent/models/__init__.py`
- Create: `src/ecox/agent/tools/__init__.py`
- Create: `src/ecox/agent/utils/__init__.py`
- Create: `tests/agent/__init__.py`
- Create: `tests/agent/test_tools/__init__.py`

**Step 1: 创建目录结构**

```bash
mkdir -p src/ecox/agent/models
mkdir -p src/ecox/agent/tools
mkdir -p src/ecox/agent/utils
mkdir -p tests/agent/test_tools
mkdir -p tests/agent/fixtures
```

**Step 2: 创建 __init__.py 文件**

```bash
touch src/ecox/agent/__init__.py
touch src/ecox/agent/models/__init__.py
touch src/ecox/agent/tools/__init__.py
touch src/ecox/agent/utils/__init__.py
touch tests/agent/__init__.py
touch tests/agent/test_tools/__init__.py
```

**Step 3: 验证目录创建**

```bash
ls -la src/ecox/agent/
ls -la tests/agent/
```

Expected: 输出显示所有目录和 __init__.py 文件已创建

**Step 4: 提交**

```bash
git add src/ecox/agent/ tests/agent/
git commit -m "feat: create agent module directory structure"
```

---

## Task 2: 实现数据模型 - Message 和 Conversation

**Files:**
- Create: `src/ecox/agent/models/message.py`
- Create: `src/ecox/agent/models/conversation.py`
- Create: `tests/agent/test_models.py`

**Step 1: 编写失败的测试 - Message 模型**

```python
# tests/agent/test_models.py
import pytest
from datetime import datetime
from ecox.agent.models.message import Message

def test_message_creation():
    """测试创建消息对象"""
    msg = Message(
        role="user",
        content="中国平安的ROE是多少？",
        session_id="test-session-123"
    )
    assert msg.role == "user"
    assert msg.content == "中国平安的ROE是多少？"
    assert msg.session_id == "test-session-123"
    assert msg.id is None  # 未保存到数据库

def test_message_with_id():
    """测试带ID的消息"""
    msg = Message(
        id=1,
        role="assistant",
        content="根据财报，中国平安的ROE为15.2%",
        conversation_id=100
    )
    assert msg.id == 1
    assert msg.role == "assistant"
    assert msg.conversation_id == 100

def test_message_invalid_role():
    """测试无效的角色"""
    with pytest.raises(ValueError):
        Message(role="invalid", content="test")
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_models.py::test_message_creation -v
```

Expected: FAIL - ModuleNotFoundError: No module named 'ecox.agent.models.message'

**Step 3: 实现最小代码**

```python
# src/ecox/agent/models/message.py
"""消息数据模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Message(Base):
    """消息模型"""
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("agent_conversations.id"), nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 运行时属性（不存数据库）
    session_id: Optional[str] = None
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None

    VALID_ROLES = {"user", "assistant", "system", "tool"}

    def __init__(
        self,
        role: str,
        content: str,
        id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        session_id: Optional[str] = None,
        tool_calls: Optional[list] = None,
        tool_call_id: Optional[str] = None
    ):
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {self.VALID_ROLES}")

        self.id = id
        self.role = role
        self.content = content
        self.conversation_id = conversation_id
        self.session_id = session_id
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id
        self.created_at = datetime.now()
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_models.py::test_message_creation -v
uv run pytest tests/agent/test_models.py::test_message_with_id -v
uv run pytest tests/agent/test_models.py::test_message_invalid_role -v
```

Expected: PASS for all three tests

**Step 5: 添加 Conversation 模型测试**

```python
# tests/agent/test_models.py 添加
from ecox.agent.models.conversation import Conversation

def test_conversation_creation():
    """测试创建对话"""
    conv = Conversation(session_id="test-session-123")
    assert conv.session_id == "test-session-123"
    assert conv.id is None

def test_conversation_with_messages():
    """测试对话关联消息"""
    conv = Conversation(
        id=1,
        session_id="test-session-123",
        metadata={"user": "test_user"}
    )
    assert conv.id == 1
    assert conv.metadata["user"] == "test_user"
```

**Step 6: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_models.py::test_conversation_creation -v
```

Expected: FAIL - ModuleNotFoundError

**Step 7: 实现 Conversation 模型**

```python
# src/ecox/agent/models/conversation.py
"""对话数据模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from .message import Base

class Conversation(Base):
    """对话模型"""
    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan")

    def __init__(
        self,
        session_id: str,
        id: Optional[int] = None,
        metadata: Optional[dict] = None
    ):
        self.id = id
        self.session_id = session_id
        self.metadata = metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
```

**Step 8: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_models.py -v
```

Expected: PASS for all 5 tests

**Step 9: 更新 models/__init__.py**

```python
# src/ecox/agent/models/__init__.py
"""Agent 数据模型"""
from .message import Message, Base
from .conversation import Conversation

__all__ = ["Message", "Conversation", "Base"]
```

**Step 10: 提交**

```bash
git add src/ecox/agent/models/ tests/agent/test_models.py
git commit -m "feat: implement Message and Conversation data models"
```

---

## Task 3: 实现 Context 和 Entities 辅助模型

**Files:**
- Create: `src/ecox/agent/models/context.py`
- Modify: `tests/agent/test_models.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_models.py 添加
from ecox.agent.models.context import Context, Entities
from ecox.agent.models.message import Message

def test_entities_creation():
    """测试实体提取结果"""
    entities = Entities()
    assert entities.stock_codes == []
    assert entities.dates == []

def test_entities_with_data():
    """测试带数据的实体"""
    entities = Entities(
        stock_codes=["600809", "SH601318"],
        dates=["2024-09-30", "2024年三季度"]
    )
    assert len(entities.stock_codes) == 2
    assert "600809" in entities.stock_codes
    assert "2024-09-30" in entities.dates

def test_context_creation():
    """测试上下文对象"""
    messages = [
        Message(role="user", content="查询中国平安", session_id="test-1")
    ]
    context = Context(
        session_id="test-1",
        history=[],
        entities=Entities(),
        current_messages=messages
    )
    assert context.session_id == "test-1"
    assert len(context.history) == 0
    assert len(context.current_messages) == 1
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_models.py::test_entities_creation -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/models/context.py
"""上下文和实体模型"""
from dataclasses import dataclass, field
from typing import List, Optional
from .message import Message

@dataclass
class Entities:
    """提取的实体"""
    stock_codes: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    company_names: List[str] = field(default_factory=list)

@dataclass
class Context:
    """对话上下文"""
    session_id: str
    history: List[Message] = field(default_factory=list)
    entities: Entities = field(default_factory=Entities)
    current_messages: List[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_models.py::test_entities_creation -v
uv run pytest tests/agent/test_models.py::test_entities_with_data -v
uv run pytest tests/agent/test_models.py::test_context_creation -v
```

Expected: PASS for all 3 tests

**Step 5: 更新 models/__init__.py**

```python
# src/ecox/agent/models/__init__.py
from .context import Context, Entities

__all__ = ["Message", "Conversation", "Base", "Context", "Entities"]
```

**Step 6: 提交**

```bash
git add src/ecox/agent/models/context.py tests/agent/test_models.py
git commit -m "feat: add Context and Entities helper models"
```

---

## Task 4: 实现工具基类

**Files:**
- Create: `src/ecox/agent/tools/base.py`
- Create: `tests/agent/test_tools/test_base.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_tools/test_base.py
import pytest
from ecox.agent.tools.base import Tool

class DummyTool(Tool):
    """测试用的虚拟工具"""

    @property
    def name(self) -> str:
        return "dummy_tool"

    @property
    def description(self) -> str:
        return "A dummy tool for testing"

    async def execute(self, **kwargs):
        return {"result": "success", **kwargs}

def test_tool_properties():
    """测试工具属性"""
    tool = DummyTool()
    assert tool.name == "dummy_tool"
    assert tool.description == "A dummy tool for testing"

def test_tool_parameters_default():
    """测试默认参数定义"""
    tool = DummyTool()
    params = tool.parameters
    assert params["type"] == "object"
    assert "properties" in params

def test_tool_execute():
    """测试工具执行"""
    import asyncio
    tool = DummyTool()
    result = asyncio.run(tool.execute(arg1="value1"))
    assert result["result"] == "success"
    assert result["arg1"] == "value1"

def test_tool_abstract_cannot_instantiate():
    """测试不能直接实例化抽象基类"""
    with pytest.raises(TypeError):
        Tool()
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_tools/test_base.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/tools/base.py
"""工具基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """工具抽象基类

    所有工具必须继承此类并实现:
    - name: 工具名称
    - description: 工具描述
    - execute: 执行逻辑
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义（OpenAI Function Calling 格式）"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具逻辑

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_tools/test_base.py -v
```

Expected: PASS for all 4 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/base.py tests/agent/test_tools/test_base.py
git commit -m "feat: implement Tool base class"
```

---

## Task 5: 实现财务分析工具

**Files:**
- Create: `src/ecox/agent/tools/financial.py`
- Create: `tests/agent/test_tools/test_financial.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_tools/test_financial.py
import pytest
from unittest.mock import AsyncMock, patch
from ecox.agent.tools.financial import FinancialAnalysisTool

@pytest.mark.asyncio
async def test_financial_tool_properties():
    """测试财务分析工具属性"""
    tool = FinancialAnalysisTool()
    assert tool.name == "financial_analysis"
    assert "财务" in tool.description or "分析" in tool.description

@pytest.mark.asyncio
async def test_financial_tool_parameters():
    """测试参数定义"""
    tool = FinancialAnalysisTool()
    params = tool.parameters
    assert params["type"] == "object"
    assert "stock_code" in params["properties"]
    assert "modules" in params["properties"]
    assert "stock_code" in params["required"]

@pytest.mark.asyncio
async def test_financial_tool_execute():
    """测试执行财务分析"""
    tool = FinancialAnalysisTool()

    # Mock the service
    with patch.object(tool, '_get_analysis_result', new_callable=AsyncMock) as mock_analysis:
        mock_analysis.return_value = {
            "stock_code": "SH601318",
            "stock_name": "中国平安",
            "roe": 15.2,
            "net_margin": 12.5
        }

        result = await tool.execute(stock_code="601318")
        assert result["stock_code"] == "SH601318"
        assert result["roe"] == 15.2
        mock_analysis.assert_called_once()
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_tools/test_financial.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/tools/financial.py
"""财务分析工具"""
from typing import Dict, Any, List
from .base import Tool
from ...utils import code_format

class FinancialAnalysisTool(Tool):
    """财务分析工具

    调用 FinancialAnalysisService 分析股票财务数据
    """

    @property
    def name(self) -> str:
        return "financial_analysis"

    @property
    def description(self) -> str:
        return "分析股票财务数据，包括ROE、毛利率、净利润、现金流、偿债能力、成长能力等指标"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码（如 601318 或 SH601318）"
                },
                "modules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "分析模块列表（profitability, cash_flow, solvency, efficiency, growth, valuation）",
                    "default": ["profitability", "solvency"]
                },
                "report_date": {
                    "type": "string",
                    "description": "报告日期（如 2024-09-30，默认最新）"
                }
            },
            "required": ["stock_code"]
        }

    async def execute(
        self,
        stock_code: str,
        modules: List[str] = None,
        report_date: str = None
    ) -> Dict[str, Any]:
        """执行财务分析

        Args:
            stock_code: 股票代码
            modules: 分析模块列表
            report_date: 报告日期

        Returns:
            财务分析结果
        """
        from ...services.financial_analysis_service import FinancialAnalysisService

        # 格式化股票代码
        formatted_code = code_format(stock_code)

        # 默认模块
        if modules is None:
            modules = ["profitability", "solvency"]

        # 调用服务
        service = FinancialAnalysisService()
        result = await self._get_analysis_result(
            service, formatted_code, modules, report_date
        )

        return result

    async def _get_analysis_result(
        self,
        service,
        stock_code: str,
        modules: List[str],
        report_date: str = None
    ) -> Dict[str, Any]:
        """获取分析结果（异步包装）"""
        # FinancialAnalysisService.calculate_metrics 是同步方法
        # 这里用 run_in_thread 执行
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: service.calculate_metrics(
                stock_code=stock_code,
                report_date=report_date,
                modules=modules
            )
        )
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_tools/test_financial.py -v
```

Expected: PASS for all 3 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/financial.py tests/agent/test_tools/test_financial.py
git commit -m "feat: implement FinancialAnalysisTool"
```

---

## Task 6: 实现行情数据工具

**Files:**
- Create: `src/ecox/agent/tools/market.py`
- Create: `tests/agent/test_tools/test_market.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_tools/test_market.py
import pytest
from ecox.agent.tools.market import MarketDataTool

@pytest.mark.asyncio
async def test_market_tool_properties():
    """测试行情工具属性"""
    tool = MarketDataTool()
    assert tool.name == "market_data"
    assert "行情" in tool.description or "股价" in tool.description

@pytest.mark.asyncio
async def test_market_tool_execute():
    """测试获取行情数据"""
    tool = MarketDataTool()

    # Mock database query
    with patch('ecox.agent.tools.market.get_db_session') as mock_db:
        mock_result = [{
            'stock_code': '601318',
            'stock_name': '中国平安',
            'close_price': 45.68,
            'change_pct': 2.35,
            'volume': 12345678,
            'update_time': '2026-03-17 15:00:00'
        }]
        mock_db.return_value.__enter__.return_value.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result[0]

        result = await tool.execute(stock_code="601318")
        assert result["stock_code"] == "601318"
        assert result["close_price"] == 45.68
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_tools/test_market.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/tools/market.py
"""行情数据工具"""
from typing import Dict, Any
from datetime import datetime, timedelta
from .base import Tool
from ...utils import code_format

class MarketDataTool(Tool):
    """行情数据工具"""

    @property
    def name(self) -> str:
        return "market_data"

    @property
    def description(self) -> str:
        return "查询股票实时行情数据，包括股价、涨跌幅、成交量等"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                }
            },
            "required": ["stock_code"]
        }

    async def execute(self, stock_code: str) -> Dict[str, Any]:
        """获取行情数据"""
        from ...database import get_db_session
        from ... import models

        formatted_code = code_format(stock_code)

        # 查询最新行情
        with get_db_session() as session:
            # 查询日线数据
            latest = session.query(models.StockDailyData).filter(
                models.StockDailyData.stock_code == formatted_code
            ).order_by(models.StockDailyData.trade_date.desc()).first()

            if not latest:
                return {
                    "error": f"未找到股票 {formatted_code} 的行情数据",
                    "stock_code": formatted_code
                }

            return {
                "stock_code": latest.stock_code,
                "stock_name": getattr(latest, 'stock_name', ''),
                "trade_date": str(latest.trade_date),
                "open_price": float(latest.open_price) if latest.open_price else None,
                "high_price": float(latest.high_price) if latest.high_price else None,
                "low_price": float(latest.low_price) if latest.low_price else None,
                "close_price": float(latest.close_price) if latest.close_price else None,
                "volume": int(latest.volume) if latest.volume else None,
                "amount": float(latest.amount) if latest.amount else None,
                "change_pct": float(latest.change_pct) if hasattr(latest, 'change_pct') and latest.change_pct else None
            }
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_tools/test_market.py -v
```

Expected: PASS for all 2 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/market.py tests/agent/test_tools/test_market.py
git commit -m "feat: implement MarketDataTool"
```

---

## Task 7: 实现数据查询工具

**Files:**
- Create: `src/ecox/agent/tools/data.py`
- Create: `tests/agent/test_tools/test_data.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_tools/test_data.py
import pytest
from ecox.agent.tools.data import DataQueryTool

@pytest.mark.asyncio
async def test_data_tool_properties():
    """测试数据查询工具属性"""
    tool = DataQueryTool()
    assert tool.name == "data_query"
    assert "查询" in tool.description or "SQL" in tool.description

@pytest.mark.asyncio
async def test_data_tool_execute_sql():
    """测试执行SQL查询"""
    tool = DataQueryTool()

    with patch('ecox.agent.tools.data.run_sql') as mock_sql:
        mock_sql.return_value = {
            "data": [
                {"stock_code": "601318", "stock_name": "中国平安", "close_price": 45.68}
            ]
        }

        result = await tool.execute(sql="SELECT * FROM stock_daily_data LIMIT 1")
        assert len(result["data"]) == 1
        assert result["data"][0]["stock_code"] == "601318"
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_tools/test_data.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/tools/data.py
"""数据查询工具"""
from typing import Dict, Any, List
from .base import Tool

class DataQueryTool(Tool):
    """数据查询工具"""

    @property
    def name(self) -> str:
        return "data_query"

    @property
    def description(self) -> str:
        return "执行SQL查询获取数据库中的数据"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL查询语句"
                }
            },
            "required": ["sql"]
        }

    async def execute(self, sql: str) -> Dict[str, Any]:
        """执行SQL查询"""
        from ...get_data import run_sql

        # 验证SQL是只读查询
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            return {
                "error": "只支持SELECT查询",
                "sql": sql
            }

        result = await self._run_query(sql)
        return result

    async def _run_query(self, sql: str) -> Dict[str, Any]:
        """异步执行查询"""
        import asyncio
        loop = asyncio.get_event_loop()
        from ...get_data import run_sql
        return await loop.run_in_executor(None, run_sql, sql)
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_tools/test_data.py -v
```

Expected: PASS for all 2 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/data.py tests/agent/test_tools/test_data.py
git commit -m "feat: implement DataQueryTool"
```

---

## Task 8: 实现回测工具

**Files:**
- Create: `src/ecox/agent/tools/backtest.py`
- Create: `tests/agent/test_tools/test_backtest.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_tools/test_backtest.py
import pytest
from ecox.agent.tools.backtest import BacktestTool

@pytest.mark.asyncio
async def test_backtest_tool_properties():
    """测试回测工具属性"""
    tool = BacktestTool()
    assert tool.name == "backtest"
    assert "回测" in tool.description

@pytest.mark.asyncio
async def test_backtest_tool_execute():
    """测试执行回测"""
    tool = BacktestTool()

    with patch('ecox.agent.tools.backtest.subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['python', 'main.py'],
            returncode=0,
            stdout=b"Sharpe Ratio: 1.5\nMax Drawdown: -10%"
        )

        result = await tool.execute(
            stock_code="601318",
            strategy="DoubleMA_Strategy",
            start_date="2023-01-01",
            end_date="2024-12-31"
        )
        assert "sharpe_ratio" in result or "output" in result
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_tools/test_backtest.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/tools/backtest.py
"""回测工具"""
import subprocess
import json
import re
from typing import Dict, Any
from .base import Tool
from ...utils import code_format

class BacktestTool(Tool):
    """策略回测工具"""

    @property
    def name(self) -> str:
        return "backtest"

    @property
    def description(self) -> str:
        return "对股票进行策略回测，支持双均线、MACD、布林带等策略"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                },
                "strategy": {
                    "type": "string",
                    "description": "策略名称（DoubleMA_Strategy, MacdCross, BollingerBandsBreakout等）",
                    "default": "DoubleMA_Strategy"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "initial_cash": {
                    "type": "number",
                    "description": "初始资金",
                    "default": 1000000
                }
            },
            "required": ["stock_code", "start_date", "end_date"]
        }

    async def execute(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        strategy: str = "DoubleMA_Strategy",
        initial_cash: float = 1000000
    ) -> Dict[str, Any]:
        """执行回测"""
        import asyncio

        formatted_code = code_format(stock_code)

        # 运行回测脚本
        cmd = [
            "uv", "run", "python", "main.py",
            "--stock", formatted_code,
            "--strategy", strategy,
            "--start", start_date,
            "--end", end_date,
            "--cash", str(initial_cash)
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/zmdsn/ecox"  # 项目根目录
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {
                    "error": "回测执行失败",
                    "stderr": stderr.decode(),
                    "stock_code": formatted_code
                }

            # 解析输出
            output = stdout.decode()
            return self._parse_backtest_output(output, formatted_code)

        except Exception as e:
            return {
                "error": str(e),
                "stock_code": formatted_code
            }

    def _parse_backtest_output(self, output: str, stock_code: str) -> Dict[str, Any]:
        """解析回测输出"""
        result = {
            "stock_code": stock_code,
            "output": output
        }

        # 尝试提取关键指标
        sharpe_match = re.search(r'Sharpe Ratio[:\s]+([-\d.]+)', output)
        if sharpe_match:
            result["sharpe_ratio"] = float(sharpe_match.group(1))

        drawdown_match = re.search(r'Max Drawdown[:\s]+([-\d.]+)%?', output)
        if drawdown_match:
            result["max_drawdown"] = float(drawdown_match.group(1))

        return match
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_tools/test_backtest.py -v
```

Expected: PASS for all 2 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/tools/backtest.py tests/agent/test_tools/test_backtest.py
git commit -m "feat: implement BacktestTool"
```

---

## Task 9: 实现 ToolRouter

**Files:**
- Create: `src/ecox/agent/tools/router.py`
- Create: `tests/agent/test_tools/test_router.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_tools/test_router.py
import pytest
from unittest.mock import AsyncMock
from ecox.agent.tools.router import ToolRouter
from ecox.agent.models.context import Context, Entities
from ecox.agent.models.message import Message

@pytest.mark.asyncio
async def test_router_initialization():
    """测试路由器初始化"""
    router = ToolRouter()
    assert len(router.tools) == 4  # financial, market, data, backtest
    assert "financial_analysis" in router.tools
    assert "market_data" in router.tools

@pytest.mark.asyncio
async def test_router_select_tools_with_stock_code():
    """测试根据股票代码选择工具"""
    router = ToolRouter()
    entities = Entities(stock_codes=["601318"])
    context = Context(
        session_id="test-1",
        entities=entities,
        current_messages=[Message(role="user", content="分析中国平安", session_id="test-1")]
    )

    tools = router._select_tools(context)
    assert "financial_analysis" in tools
    assert "market_data" in tools

@pytest.mark.asyncio
async def test_router_execute():
    """测试执行工具"""
    router = ToolRouter()

    # Mock tools
    for tool_name, tool in router.tools.items():
        tool.execute = AsyncMock(return_value={"mock": "result"})

    context = Context(
        session_id="test-1",
        entities=Entities(stock_codes=["601318"]),
        current_messages=[Message(role="user", content="分析中国平安", session_id="test-1")]
    )

    results = await router.execute(context)
    assert "financial_analysis" in results
    assert "market_data" in results
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_tools/test_router.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/tools/router.py
"""工具路由器"""
import logging
from typing import Dict, Any, List
from .financial import FinancialAnalysisTool
from .market import MarketDataTool
from .data import DataQueryTool
from .backtest import BacktestTool

logger = logging.getLogger(__name__)

class ToolRouter:
    """工具路由和编排

    根据对话上下文选择并执行相应的工具
    """

    def __init__(self):
        """初始化路由器"""
        self.tools: Dict[str, Any] = {
            "financial_analysis": FinancialAnalysisTool(),
            "market_data": MarketDataTool(),
            "data_query": DataQueryTool(),
            "backtest": BacktestTool(),
        }

    async def execute(self, context) -> Dict[str, Any]:
        """根据上下文执行工具

        Args:
            context: 对话上下文

        Returns:
            工具执行结果字典
        """
        # 选择需要调用的工具
        tools_to_call = self._select_tools(context)

        results = {}
        for tool_name in tools_to_call:
            tool = self.tools[tool_name]

            # 准备参数
            kwargs = self._prepare_args(tool, context)

            # 执行工具
            try:
                result = await tool.execute(**kwargs)
                results[tool_name] = result
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                results[tool_name] = {"error": str(e)}

        return results

    def _select_tools(self, context) -> List[str]:
        """根据上下文选择工具"""
        tools = []

        # 有股票代码实体
        if context.entities.stock_codes:
            tools.append("financial_analysis")
            tools.append("market_data")

        # 有日期实体
        if context.entities.dates:
            tools.append("data_query")

        # 检查关键词
        content = " ".join([msg.content for msg in context.current_messages])

        if "回测" in content or "策略" in content:
            tools.append("backtest")

        if "查询" in content or "SQL" in content or "sql" in content.lower():
            if "data_query" not in tools:
                tools.append("data_query")

        return tools

    def _prepare_args(self, tool, context) -> Dict[str, Any]:
        """准备工具参数"""
        if tool.name == "financial_analysis":
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None,
                "modules": ["profitability", "solvency", "cash_flow"]
            }

        elif tool.name == "market_data":
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None
            }

        elif tool.name == "backtest":
            # 从实体中提取日期
            dates = context.entities.dates
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None,
                "start_date": dates[0] if len(dates) > 0 else "2023-01-01",
                "end_date": dates[1] if len(dates) > 1 else "2024-12-31"
            }

        elif tool.name == "data_query":
            # 构建简单查询
            stock_code = context.entities.stock_codes[0] if context.entities.stock_codes else None
            if stock_code:
                return {
                    "sql": f"SELECT * FROM stock_daily_data WHERE stock_code = '{stock_code}' ORDER BY trade_date DESC LIMIT 10"
                }
            return {
                "sql": "SELECT * FROM stock_daily_data LIMIT 10"
            }

        return {}
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_tools/test_router.py -v
```

Expected: PASS for all 3 tests

**Step 5: 更新 tools/__init__.py**

```python
# src/ecox/agent/tools/__init__.py
from .base import Tool
from .financial import FinancialAnalysisTool
from .market import MarketDataTool
from .data import DataQueryTool
from .backtest import BacktestTool
from .router import ToolRouter

__all__ = [
    "Tool",
    "FinancialAnalysisTool",
    "MarketDataTool",
    "DataQueryTool",
    "BacktestTool",
    "ToolRouter"
]
```

**Step 6: 提交**

```bash
git add src/ecox/agent/tools/router.py tests/agent/test_tools/test_router.py src/ecox/agent/tools/__init__.py
git commit -m "feat: implement ToolRouter for tool orchestration"
```

---

## Task 10: 实现 ConversationManager

**Files:**
- Create: `src/ecox/agent/conversation.py`
- Create: `tests/agent/test_conversation.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_conversation.py
import pytest
from unittest.mock import Mock, patch
from ecox.agent.conversation import ConversationManager
from ecox.agent.models.message import Message
from ecox.agent.models.context import Context

@pytest.mark.asyncio
async def test_conversation_manager_init():
    """测试初始化"""
    manager = ConversationManager(max_history=10)
    assert manager.max_history == 10

@pytest.mark.asyncio
async def test_get_context():
    """测试获取上下文"""
    manager = ConversationManager()

    messages = [
        Message(role="user", content="中国平安的ROE是多少？", session_id="test-1")
    ]

    # Mock _load_history
    with patch.object(manager, '_load_history', return_value=[]):
        context = await manager.get_context(messages)

    assert context.session_id == "test-1"
    assert context.current_messages == messages

@pytest.mark.asyncio
async def test_extract_entities():
    """测试实体提取"""
    manager = ConversationManager()

    messages = [
        Message(role="user", content="查询中国平安601318和SH600809的2024年三季度财报", session_id="test-1")
    ]

    entities = manager._extract_entities(messages)

    assert "601318" in entities.stock_codes
    assert "SH600809" in entities.stock_codes
    assert "中国平安" in entities.company_names or "中国平安" in entities.stock_codes
    assert "2024年三季度" in entities.dates or "2024" in entities.dates

@pytest.mark.asyncio
async def test_save_conversation():
    """测试保存对话"""
    manager = ConversationManager()

    messages = [
        Message(role="user", content="中国平安的ROE？", session_id="test-1")
    ]

    # Mock database session
    with patch('ecox.agent.conversation.get_db_session') as mock_db:
        mock_session = Mock()
        mock_db.return_value.__enter__.return_value = mock_session

        # Mock query returns None (new conversation)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        await manager.save("test-1", messages, "根据财报，ROE为15.2%")

        # 验证创建了新对话
        assert mock_session.add.called
        assert mock_session.commit.called
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_conversation.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/conversation.py
"""对话管理器"""
import logging
import re
from typing import List
from .models import Conversation, Message, Context, Entities
from ...database import get_db_session

logger = logging.getLogger(__name__)

class ConversationManager:
    """对话状态和历史管理"""

    def __init__(self, max_history: int = 20):
        """初始化对话管理器

        Args:
            max_history: 最大历史消息数
        """
        self.max_history = max_history

    async def get_context(self, messages: List[Message]) -> Context:
        """提取对话上下文

        Args:
            messages: 当前消息列表

        Returns:
            包含历史和实体的上下文对象
        """
        session_id = messages[0].session_id

        # 获取历史对话
        history = await self._load_history(session_id)

        # 提取实体
        entities = self._extract_entities(messages + history)

        return Context(
            session_id=session_id,
            history=history[-self.max_history:] if history else [],
            entities=entities,
            current_messages=messages
        )

    async def _load_history(self, session_id: str) -> List[Message]:
        """从数据库加载历史"""
        try:
            with get_db_session() as session:
                # 获取最近的对话
                conv = session.query(Conversation).filter_by(
                    session_id=session_id
                ).order_by(Conversation.updated_at.desc()).first()

                if not conv:
                    return []

                # 加载消息
                messages = session.query(Message).filter_by(
                    conversation_id=conv.id
                ).order_by(Message.created_at.asc()).all()

                return messages
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def _extract_entities(self, messages: List[Message]) -> Entities:
        """提取对话中的实体

        Args:
            messages: 消息列表

        Returns:
            提取的实体对象
        """
        entities = Entities()

        content = " ".join([msg.content for msg in messages])

        # 提取股票代码
        # 匹配：600809, SH600809, SH600809.SZ
        stock_patterns = [
            r'\b[0-9]{6}\b',  # 6位数字
            r'\bSH[0-9]{6}\b',  # SH + 6位
            r'\bSZ[0-9]{6}\b',  # SZ + 6位
            r'\bBJ[0-9]{6}\b',  # BJ + 6位
        ]

        for pattern in stock_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in entities.stock_codes:
                    entities.stock_codes.append(match)

        # 提取中文名称（2-4字，可能是公司名）
        name_pattern = r'[\u4e00-\u9fff]{2,4}'
        chinese_names = re.findall(name_pattern, content)
        for name in chinese_names:
            if len(name) >= 2 and name not in entities.company_names:
                entities.company_names.append(name)

        # 提取日期
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD 或 YYYY-M-D
            r'\d{4}年\d{1,2}季度',  # YYYY年Q季度
            r'\d{4}年\d{1,2}月',  # YYYY年M月
            r'\d{4}半年报',  # YYYY半年报
            r'\d{4}年报',  # YYYY年报
            r'\d{4}一季报',  # YYYY一季报
            r'\d{4}中报',  # YYYY中报
            r'\d{4}三季报',  # YYYY三季报
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in entities.dates:
                    entities.dates.append(match)

        return entities

    async def save(
        self,
        session_id: str,
        messages: List[Message],
        response: str
    ):
        """保存对话到数据库

        Args:
            session_id: 会话ID
            messages: 用户消息
            response: 助手回复
        """
        try:
            with get_db_session() as session:
                # 获取或创建对话
                conv = session.query(Conversation).filter_by(
                    session_id=session_id
                ).first()

                if not conv:
                    conv = Conversation(session_id=session_id)
                    session.add(conv)
                    session.flush()

                # 保存用户消息
                for msg in messages:
                    db_msg = Message(
                        conversation_id=conv.id,
                        role=msg.role,
                        content=msg.content
                    )
                    session.add(db_msg)

                # 保存助手回复
                response_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=response
                )
                session.add(response_msg)

                from datetime import datetime
                conv.updated_at = datetime.now()

                session.commit()
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            raise
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_conversation.py -v
```

Expected: PASS for all 4 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/conversation.py tests/agent/test_conversation.py
git commit -m "feat: implement ConversationManager"
```

---

## Task 11: 实现 EcoxA 核心智能体类

**Files:**
- Create: `src/ecox/agent/agent.py`
- Create: `tests/agent/test_agent.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_agent.py
import pytest
from unittest.mock import AsyncMock, patch, Mock
from ecox.agent.agent import EcoxA
from ecox.agent.models.message import Message

@pytest.mark.asyncio
async def test_agent_initialization():
    """测试智能体初始化"""
    agent = EcoxA(model="gpt-4")
    assert agent.model == "gpt-4"
    assert agent.max_history == 20
    assert agent.conversation is not None
    assert agent.tool_router is not None

@pytest.mark.asyncio
async def test_agent_needs_tools():
    """测试工具调用判断"""
    agent = EcoxA()

    # 包含财务关键词
    context = Mock()
    context.history = [
        Message(role="user", content="中国平安的ROE是多少？", session_id="test-1")
    ]

    result = agent._needs_tools(context)
    assert result is True

@pytest.mark.asyncio
async def test_agent_chat_without_tools():
    """测试不需要工具的对话"""
    agent = EcoxA()

    messages = [
        Message(role="user", content="你好", session_id="test-1")
    ]

    # Mock get_context 和 _completion
    with patch.object(agent.conversation, 'get_context', new_callable=AsyncMock) as mock_context:
        mock_context.return_value = Mock(
            session_id="test-1",
            history=[],
            entities=Mock(stock_codes=[]),
            current_messages=messages
        )

        with patch.object(agent, '_completion', new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = "你好！我是Ecox AI助手。"

            with patch.object(agent.conversation, 'save', new_callable=AsyncMock):
                response = await agent.chat(messages)

    assert response == "你好！我是Ecox AI助手。"

@pytest.mark.asyncio
async def test_agent_build_messages():
    """测试构建消息列表"""
    agent = EcoxA()

    context = Mock()
    context.history = [
        Message(role="user", content="中国平安的ROE是多少？", session_id="test-1")
    ]

    messages = agent._build_messages(context, {})

    assert len(messages) == 2  # system + user
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_agent.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/agent.py
"""Ecox AI 智能体核心类"""
import logging
import json
import uuid
from typing import List, AsyncIterator
import httpx
from .conversation import ConversationManager
from .tools import ToolRouter
from .models import Message, Context

logger = logging.getLogger(__name__)

class EcoxA:
    """Ecox AI 智能体

    提供全功能的 A 股投资咨询服务，支持：
    - 多轮对话
    - 工具调用
    - 上下文理解
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_history: int = 20,
        timeout: int = 30,
        litellm_base_url: str = "http://localhost:8000"
    ):
        """初始化智能体

        Args:
            model: 默认使用的模型
            max_history: 最大历史消息数
            timeout: API 调用超时时间
            litellm_base_url: LiteLLM 服务地址
        """
        self.model = model
        self.max_history = max_history
        self.timeout = timeout
        self.litellm_base_url = litellm_base_url
        self.conversation = ConversationManager(max_history)
        self.tool_router = ToolRouter()
        self.client = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self,
        messages: List[Message],
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理对话请求

        Args:
            messages: 消息列表
            stream: 是否流式输出

        Returns:
            响应内容或流式迭代器
        """
        # 1. 提取上下文
        context = await self.conversation.get_context(messages)

        # 2. 判断是否需要调用工具
        if self._needs_tools(context):
            # 3. 执行工具调用
            tool_results = await self._execute_tools(context)

            # 4. 生成回复（包含工具结果）
            response = await self._generate_with_tools(
                context, tool_results, stream=stream
            )
        else:
            # 5. 直接生成回复
            response = await self._generate_direct(context, stream=stream)

        # 6. 保存对话历史
        await self.conversation.save(
            session_id=messages[0].session_id,
            messages=messages,
            response=response
        )

        return response

    def _needs_tools(self, context: Context) -> bool:
        """判断是否需要调用工具"""
        # 简单的关键词匹配
        keywords = {
            "财务": ["ROE", "毛利率", "净利润", "现金流", "资产", "负债"],
            "行情": ["股价", "涨跌幅", "成交量", "最新", "开盘", "收盘"],
            "回测": ["回测", "策略", "收益率"],
            "查询": ["查询", "数据", "SQL", "财报"],
        }

        content = " ".join([msg.content for msg in context.history + context.current_messages])

        for category, terms in keywords.items():
            if any(term in content for term in terms):
                return True

        # 检查是否有股票代码
        if context.entities.stock_codes:
            return True

        return False

    async def _execute_tools(self, context: Context) -> dict:
        """执行工具调用"""
        try:
            return await self.tool_router.execute(context)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}

    async def _generate_with_tools(
        self,
        context: Context,
        tool_results: dict,
        stream: bool
    ) -> AsyncIterator[str] | str:
        """使用工具结果生成回复"""
        messages = self._build_messages(context, tool_results)

        if stream:
            return self._stream_completion(messages)
        else:
            return await self._completion(messages)

    async def _generate_direct(
        self,
        context: Context,
        stream: bool
    ) -> AsyncIterator[str] | str:
        """直接生成回复"""
        messages = self._build_messages(context, {})

        if stream:
            return self._stream_completion(messages)
        else:
            return await self._completion(messages)

    def _build_messages(
        self,
        context: Context,
        tool_results: dict
    ) -> List[dict]:
        """构建消息列表"""
        from .utils.prompts import SYSTEM_PROMPT

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 添加历史对话
        for msg in context.history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 添加当前消息
        for msg in context.current_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 添加工具结果（如果有）
        if tool_results:
            tool_content = json.dumps(tool_results, ensure_ascii=False, indent=2)
            messages.append({
                "role": "system",
                "content": f"工具调用结果：\n{tool_content}"
            })

        return messages

    async def _completion(self, messages: List[dict]) -> str:
        """调用模型生成回复"""
        try:
            # 调用 LiteLLM
            url = f"{self.litellm_base_url}/v1/chat/completions"
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }

            logger.info(f"Calling LiteLLM: {url}")
            logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False)}")

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(f"Model invocation failed: {e}")
            return f"抱歉，调用模型服务时出错：{str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"抱歉，发生意外错误：{str(e)}"

    async def _stream_completion(self, messages: List[dict]) -> AsyncIterator[str]:
        """流式生成回复"""
        # 暂时返回非流式结果
        # TODO: 实现真正的 SSE 流式响应
        result = await self._completion(messages)
        yield result

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_agent.py -v
```

Expected: PASS for all 4 tests

**Step 5: 提交**

```bash
git add src/ecox/agent/agent.py tests/agent/test_agent.py
git commit -m "feat: implement EcoxA core agent class"
```

---

## Task 12: 实现提示词模板

**Files:**
- Create: `src/ecox/agent/utils/prompts.py`

**Step 1: 创建提示词文件**

```python
# src/ecox/agent/utils/prompts.py
"""提示词模板"""

SYSTEM_PROMPT = """你是一位专业的 A 股投资分析助手，名为 Ecox AI。你的职责是为用户提供准确、及时的股票分析和投资建议。

## 核心能力

1. **财务分析** - 能够分析上市公司的财务报表，包括：
   - 盈利能力指标（ROE、ROA、毛利率、净利率等）
   - 偿债能力指标（资产负债率、流动比率、速动比率等）
   - 营运能力指标（存货周转率、应收账款周转率等）
   - 成长能力指标（收入增长率、利润增长率等）
   - 现金流分析

2. **行情分析** - 提供股票价格、涨跌幅、成交量等实时行情数据

3. **策略回测** - 支持多种技术指标的策略回测，包括：
   - 双均线交叉策略
   - MACD 策略
   - 布林带突破策略
   - RSI 均值回归策略

4. **数据查询** - 根据用户需求查询历史数据

## 回答原则

1. **准确性优先** - 基于真实数据回答，不编造信息
2. **客观中立** - 提供客观分析，不给出绝对化的投资建议
3. **风险提示** - 涉及投资建议时，提醒用户注意风险
4. **简洁明了** - 用通俗易懂的语言解释专业概念
5. **数据支撑** - 回答时引用具体数据和来源

## 对话风格

- 专业且友好
- 主动追问关键信息（如具体股票代码、时间范围等）
- 使用 Markdown 格式美化输出（表格、列表、代码块等）
- 适当使用表情符号增加亲和力

## 注意事项

- 股票代码需要 6 位数字（如 601318）
- 可以接受带交易所前缀的代码（如 SH601318、SZ000001）
- 遇到数据缺失时，诚实告知用户
- 不懂的问题不要强行回答

现在，请开始为用户服务吧！
"""
```

**Step 2: 提交**

```bash
git add src/ecox/agent/utils/prompts.py
git commit -m "feat: add system prompt template"
```

---

## Task 13: 实现 FastAPI 服务器

**Files:**
- Create: `src/ecox/agent/server.py`
- Create: `tests/agent/test_api.py`

**Step 1: 编写失败的测试**

```python
# tests/agent/test_api.py
import pytest
from fastapi.testclient import TestClient
from ecox.agent.server import app

client = TestClient(app)

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ecox-ai"

def test_list_models():
    """测试列出模型端点"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0

def test_chat_completions():
    """测试聊天补全端点"""
    request_data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "你好"}
        ]
    }

    # Mock agent
    with patch('ecox.agent.server.EcoxA') as MockAgent:
        mock_agent = Mock()
        mock_agent.chat = Mock(return_value="你好！我是Ecox AI助手。")
        MockAgent.return_value = mock_agent

        response = client.post("/v1/chat/completions", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/agent/test_api.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现最小代码**

```python
# src/ecox/agent/server.py
"""FastAPI 服务器 - OpenAI 兼容接口"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx

from .agent import EcoxA
from .models.message import Message

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ecox AI API",
    description="A 股投资智能体 API - OpenAI 兼容接口",
    version="1.0.0"
)

# 请求和响应模型
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=32000)
    stream: Optional[bool] = False
    tools: Optional[List[dict]] = None

class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[ChatUsage] = None

def estimate_tokens(text_list: List[ChatMessage]) -> int:
    """简单的 token 估算"""
    total_chars = sum(len(msg.content) for msg in text_list)
    return total_chars // 2  # 粗略估算：2 字符 ≈ 1 token

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ecox-ai",
        "version": "1.0.0"
    }

# 模型列表端点
@app.get("/v1/models")
async def list_models():
    """列出可用模型"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4",
                "object": "model",
                "owned_by": "ecox"
            },
            {
                "id": "gpt-4-turbo",
                "object": "model",
                "owned_by": "ecox"
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "owned_by": "ecox"
            },
            {
                "id": "claude-3-sonnet-20241022",
                "object": "model",
                "owned_by": "ecox"
            }
        ]
    }

# 核心 API 端点
@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """OpenAI 兼容的聊天接口

    这是与 OpenAI Chat Completions API 完全兼容的接口。
    支持：
    - 多轮对话
    - 流式输出（基础支持）
    - 工具调用（通过 Agent 自动判断）
    """
    try:
        # 转换消息格式
        agent_messages = []
        session_id = request.messages[0].session_id or str(uuid.uuid4())

        for msg in request.messages:
            agent_messages.append(
                Message(
                    role=msg.role,
                    content=msg.content,
                    session_id=session_id
                )
            )

        # 创建 Agent 实例
        agent = EcoxA(model=request.model)

        # 处理对话
        response_content = await agent.chat(
            messages=agent_messages,
            stream=request.stream
        )

        # 构建响应
        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content,
                    "session_id": session_id
                },
                "finish_reason": "stop"
            }],
            usage=ChatUsage(
                prompt_tokens=estimate_tokens(request.messages),
                completion_tokens=estimate_tokens([ChatMessage(role="assistant", content=response_content)]),
                total_tokens=estimate_tokens(request.messages) + estimate_tokens([ChatMessage(role="assistant", content=response_content)])
            )
        )

    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": str(exc),
                "type": exc.__class__.__name__
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/agent/test_api.py -v
```

Expected: PASS for all 3 tests

**Step 5: 更新依赖**

```bash
uv add fastapi uvicorn[standard] httpx
```

**Step 6: 提交**

```bash
git add src/ecox/agent/server.py tests/agent/test_api.py pyproject.toml
git commit -m "feat: implement FastAPI server with OpenAI-compatible endpoints"
```

---

## Task 14: 创建数据库表初始化脚本

**Files:**
- Create: `scripts/init_agent_tables.py`

**Step 1: 创建初始化脚本**

```python
# scripts/init_agent_tables.py
"""初始化 Agent 相关数据库表"""
import sys
from pathlib import Path

# 添加项目根目录到路径
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from ecox.agent.models import Base
from ecox.database import engine

def init_tables():
    """创建 Agent 相关数据表"""
    print("Creating Agent tables...")

    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Agent tables created successfully!")
        print("  - agent_conversations")
        print("  - agent_messages")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

    return True

if __name__ == "__main__":
    success = init_tables()
    sys.exit(0 if success else 1)
```

**Step 2: 运行脚本测试**

```bash
uv run python scripts/init_agent_tables.py
```

Expected: 输出显示表创建成功

**Step 3: 提交**

```bash
git add scripts/init_agent_tables.py
git commit -m "feat: add database initialization script for Agent tables"
```

---

## Task 15: 创建服务器启动脚本

**Files:**
- Create: `scripts/start_agent_server.py`

**Step 1: 创建启动脚本**

```python
# scripts/start_agent_server.py
"""启动 Ecox AI Agent 服务器"""
import sys
from pathlib import Path

# 添加项目根目录到路径
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

import uvicorn

def start_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    reload: bool = False
):
    """启动 FastAPI 服务器

    Args:
        host: 监听地址
        port: 监听端口
        reload: 是否启用热重载（开发模式）
    """
    print(f"Starting Ecox AI Agent server...")
    print(f"Address: http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")

    uvicorn.run(
        "ecox.agent.server:app",
        host=host,
        port=port,
        reload=reload
    )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ecox AI Agent Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    start_server(host=args.host, port=args.port, reload=args.reload)
```

**Step 2: 验证启动脚本**

```bash
# 检查脚本语法（不实际启动）
uv run python scripts/start_agent_server.py --help
```

Expected: 显示帮助信息

**Step 3: 提交**

```bash
git add scripts/start_agent_server.py
git commit -m "feat: add Agent server startup script"
```

---

## Task 16: 创建 LiteLLM 配置和启动脚本

**Files:**
- Create: `scripts/start_litellm_proxy.py`
- Create: `litellm_config.yaml`

**Step 1: 创建 LiteLLM 配置**

```yaml
# litellm_config.yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY

  - model_name: gpt-4-turbo
    litellm_params:
      model: openai/gpt-4-turbo
      api_key: os.environ/OPENAI_API_KEY

  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-3-sonnet-20241022
    litellm_params:
      model: anthropic/claude-3-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

litellm_settings:
  drop_params: true
  set_verbose: false
  success_callback: ["langfuse"]
```

**Step 2: 创建启动脚本**

```python
# scripts/start_litellm_proxy.py
"""启动 LiteLLM 代理服务器"""
import subprocess
import sys
from pathlib import Path

def start_litellm(
    host: str = "0.0.0.0",
    port: int = 8000,
    config: str = "litellm_config.yaml"
):
    """启动 LiteLLM 代理

    Args:
        host: 监听地址
        port: 监听端口
        config: 配置文件路径
    """
    config_path = Path(__file__).parent.parent / config

    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        print("Please create litellm_config.yaml with your API keys")
        return False

    print(f"Starting LiteLLM proxy...")
    print(f"Address: http://{host}:{port}")
    print(f"Config: {config_path}")

    cmd = [
        "litellm",
        "--config", str(config_path),
        "--port", str(port),
        "--host", host
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start LiteLLM: {e}")
        return False
    except KeyboardInterrupt:
        print("\n✓ LiteLLM stopped")
        return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LiteLLM Proxy Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", default="litellm_config.yaml", help="Config file path")

    args = parser.parse_args()

    success = start_litellm(host=args.host, port=args.port, config=args.config)
    sys.exit(0 if success else 1)
```

**Step 3: 检查 litellm 是否已安装**

```bash
uv litellm --version
```

If not found:
```bash
uv add litellm
```

**Step 4: 提交**

```bash
git add scripts/start_litellm_proxy.py litellm_config.yaml
git commit -m "feat: add LiteLLM proxy configuration and startup script"
```

---

## Task 17: 创建集成测试

**Files:**
- Create: `tests/agent/test_integration.py`

**Step 1: 编写集成测试**

```python
# tests/agent/test_integration.py
"""Agent 集成测试"""
import pytest
from unittest.mock import AsyncMock, patch
from ecox.agent.agent import EcoxA
from ecox.agent.models.message import Message

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_conversation_flow():
    """测试完整对话流程"""
    agent = EcoxA(model="gpt-4")

    messages = [
        Message(role="user", content="中国平安的ROE是多少？", session_id="test-integration-1")
    ]

    # Mock conversation manager
    with patch.object(agent.conversation, 'get_context', new_callable=AsyncMock) as mock_get_context:
        from ecox.agent.models.context import Context, Entities

        mock_get_context.return_value = Context(
            session_id="test-integration-1",
            history=[],
            entities=Entities(stock_codes=["601318"]),
            current_messages=messages
        )

        # Mock tool execution
        with patch.object(agent, '_execute_tools', new_callable=AsyncMock) as mock_tools:
            mock_tools.return_value = {
                "financial_analysis": {
                    "stock_code": "SH601318",
                    "stock_name": "中国平安",
                    "roe": 15.2
                }
            }

            # Mock model completion
            with patch.object(agent, '_completion', new_callable=AsyncMock) as mock_completion:
                mock_completion.return_value = "根据财报数据，中国平安（SH601318）的最新ROE为15.2%。"

                # Mock save
                with patch.object(agent.conversation, 'save', new_callable=AsyncMock):
                    response = await agent.chat(messages)

    assert "15.2%" in response or "中国平安" in response

@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_turn_conversation():
    """测试多轮对话"""
    agent = EcoxA()

    # 第一轮
    messages1 = [
        Message(role="user", content="查询中国平安", session_id="test-multi-1")
    ]

    with patch.object(agent.conversation, 'get_context', new_callable=AsyncMock) as mock_ctx:
        from ecox.agent.models.context import Context, Entities
        mock_ctx.return_value = Context(
            session_id="test-multi-1",
            history=[],
            entities=Entities(stock_codes=["601318"]),
            current_messages=messages1
        )

        with patch.object(agent, '_execute_tools', new_callable=AsyncMock) as mock_tools:
            mock_tools.return_value = {"market_data": {"close_price": 45.68}}

            with patch.object(agent, '_completion', new_callable=AsyncMock) as mock_comp:
                mock_comp.return_value = "中国平安最新股价为45.68元。"

                with patch.object(agent.conversation, 'save', new_callable=AsyncMock):
                    response1 = await agent.chat(messages1)

    assert "45.68" in response1 or "中国平安" in response1
```

**Step 2: 运行集成测试**

```bash
uv run pytest tests/agent/test_integration.py -v -m integration
```

Expected: PASS

**Step 3: 提交**

```bash
git add tests/agent/test_integration.py
git commit -m "feat: add integration tests for Agent"
```

---

## Task 18: 创建使用文档

**Files:**
- Create: `docs/agent-usage.md`

**Step 1: 编写使用文档**

```markdown
# Ecox AI Agent 使用指南

## 概述

Ecox AI Agent 是一个全功能的 A 股投资智能体系统，提供与 OpenAI API 兼容的接口。

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置 API Keys

创建 `.env` 文件：

```bash
# OpenAI API Key（用于 GPT 模型）
OPENAI_API_KEY=sk-xxx

# Anthropic API Key（用于 Claude 模型）
ANTHROPIC_API_KEY=sk-ant-xxx
```

### 3. 初始化数据库

```bash
uv run python scripts/init_agent_tables.py
```

### 4. 启动 LiteLLM 代理（新终端）

```bash
uv run python scripts/start_litellm_proxy.py
```

### 5. 启动 Ecox AI 服务（原终端）

```bash
uv run python scripts/start_agent_server.py --reload
```

服务将在 `http://localhost:8080` 启动。

## 使用示例

### 使用 OpenAI Python SDK

```python
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="dummy"  # 本地服务不需要真实 key
)

# 简单对话
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": "中国平安的ROE是多少？"
    }]
)

print(response.choices[0].message.content)

# 多轮对话
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "查询中国平安"},
        {"role": "assistant", "content": "中国平安（SH601318）最新股价为45.68元。"},
        {"role": "user", "content": "它的财务状况怎么样？"}
    ]
)

print(response.choices[0].message.content)
```

### 使用 cURL

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "中国平安的ROE是多少？"}
    ]
  }'
```

### 使用 LangChain

```python
from langchain_openai import ChatOpenAI

# 初始化
llm = ChatOpenAI(
    model="gpt-4",
    base_url="http://localhost:8080/v1",
    api_key="dummy",
    temperature=0.7
)

# 调用
response = llm.invoke("分析一下中国平安的投资价值")
print(response.content)
```

## API 端点

### `/v1/chat/completions`

OpenAI 兼容的聊天补全接口。

**请求体：**

```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "你是一个投资助手"},
    {"role": "user", "content": "查询中国平安"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false
}
```

**响应体：**

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "根据最新数据..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 50,
    "total_tokens": 70
  }
}
```

### `/health`

健康检查端点。

### `/v1/models`

列出可用模型。

## 功能说明

### 自动工具调用

Agent 会自动判断是否需要调用工具，无需手动指定。

支持的工具：
- **财务分析** - ROE、毛利率、现金流等财务指标
- **行情查询** - 股价、涨跌幅、成交量
- **数据查询** - SQL 查询历史数据
- **策略回测** - 双均线、MACD 等策略回测

### 多轮对话

Agent 会自动保存对话历史，支持上下文理解。

### 实体提取

自动从对话中提取：
- 股票代码（601318、SH601318）
- 公司名称（中国平安）
- 日期（2024-09-30、2024年三季度）

## 常见问题

### 1. LiteLLM 启动失败

检查 API keys 是否正确配置：

```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### 2. 数据库连接失败

确保 PostgreSQL 服务正在运行，并检查配置。

### 3. 工具调用失败

检查相关服务是否可用：
- 财务数据是否已下载
- 行情数据是否已采集

## 开发模式

启动开发服务器（支持热重载）：

```bash
# Agent 服务
uv run python scripts/start_agent_server.py --reload

# LiteLLM 代理
litellm --config litellm_config.yaml --port 8000
```

## 测试

运行所有测试：

```bash
uv run pytest tests/agent/ -v
```

运行集成测试：

```bash
uv run pytest tests/agent/test_integration.py -v -m integration
```

## 架构说明

详见设计文档：`docs/plans/2026-03-17-ecox-ai-agent-design.md`
```

**Step 2: 提交**

```bash
git add docs/agent-usage.md
git commit -m "docs: add Agent usage guide"
```

---

## Task 19: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 添加 Agent 相关说明**

在 CLAUDE.md 的"代码架构"部分后添加：

```markdown
### AI Agent 模块（src/ecox/agent/）

- **src/ecox/agent/agent.py** - EcoxA 核心智能体类
  - 对话处理
  - 工具调用协调
  - 上下文管理

- **src/ecox/agent/conversation.py** - ConversationManager
  - 对话历史存储
  - 上下文提取
  - 实体识别

- **src/ecox/agent/tools/** - 工具系统
  - `financial.py` - 财务分析工具
  - `market.py` - 行情数据工具
  - `data.py` - 数据查询工具
  - `backtest.py` - 回测工具
  - `router.py` - 工具路由器

- **src/ecox/agent/server.py** - FastAPI 服务器
  - OpenAI 兼容接口（/v1/chat/completions）
  - 支持流式输出
  - 自动工具调用
```

在"常用命令"部分添加：

```markdown
### Agent 相关命令

```bash
# 初始化 Agent 数据库表
uv run python scripts/init_agent_tables.py

# 启动 Agent 服务
uv run python scripts/start_agent_server.py

# 启动 LiteLLM 代理
uv run python scripts/start_litellm_proxy.py

# 测试 Agent API
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "你好"}]}'
```
```

**Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Agent information"
```

---

## Task 20: 运行完整测试套件并验证

**Files:**
- None (验证任务)

**Step 1: 运行所有 Agent 测试**

```bash
uv run pytest tests/agent/ -v --tb=short
```

Expected: 所有测试通过

**Step 2: 检查测试覆盖率**

```bash
uv run pytest tests/agent/ --cov=src/ecox/agent --cov-report=term-missing
```

Expected: 覆盖率 > 70%

**Step 3: 验证数据库表**

```bash
uv run python -c "
from ecox.database import engine
from ecox.agent.models import Base
print('Tables:', [t.name for t in Base.metadata.tables.values()])
"
```

Expected: 输出包含 agent_conversations 和 agent_messages

**Step 4: 检查代码导入**

```bash
uv run python -c "
from ecox.agent.agent import EcoxA
from ecox.agent.server import app
from ecox.agent.tools import ToolRouter
print('All imports successful!')
"
```

Expected: 无错误

**Step 5: 提交**

```bash
git add .
git commit -m "test: verify complete Agent implementation"
```

---

## 执行说明

实施计划包含 20 个任务，涵盖：
1. 目录结构创建
2. 数据模型实现（Message, Conversation, Context, Entities）
3. 工具系统实现（基类 + 4 个具体工具 + 路由器）
4. ConversationManager 实现
5. EcoxA 核心智能体实现
6. FastAPI 服务器实现
7. 数据库初始化脚本
8. 启动脚本（Agent 和 LiteLLM）
9. 集成测试
10. 文档更新

每个任务遵循 TDD 流程：写测试 → 运行失败 → 实现代码 → 运行通过 → 提交。

**预计时间:** 约 4-6 小时（如果按顺序执行）

**下一步:**
1. 选择执行模式（subagent-driven 或 parallel session）
2. 开始执行任务
3. 完成后启动服务并测试

**所需依赖:**
- fastapi
- uvicorn[standard]
- httpx
- litellm

启动前需要:
1. 配置 OpenAI/Anthropic API keys
2. 初始化数据库表
3. 启动 LiteLLM 代理
4. 启动 Agent 服务
