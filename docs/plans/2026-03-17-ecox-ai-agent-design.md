# Ecox AI 智能体系统设计文档

**日期**: 2026-03-17
**作者**: Claude
**版本**: 1.0
**状态**: 待实施

---

## 1. 项目概述

### 1.1 目标

构建一个全功能的 A 股投资智能体系统，具备以下能力：
- 支持多轮对话和上下文理解
- 可调用项目的所有服务（财务分析、数据采集、策略回测、实时行情等）
- 提供与 OpenAI API 兼容的接口，方便集成
- 弃用现有的 FastMCP 框架，使用自定义架构

### 1.2 核心特性

1. **智能对话** - 理解用户意图，提供专业投资建议
2. **工具调用** - 自动调用后台服务获取数据和分析
3. **上下文管理** - 保存对话历史，支持多轮对话
4. **API 兼容** - 完全兼容 OpenAI Chat Completions API
5. **本地部署** - 作为本地服务运行，支持本地模型

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端层                                │
│  - OpenAI Python SDK (langchain/openai)                   │
│  - OpenAI TypeScript SDK (前端应用)                        │
│  - cURL/Postman (API 测试)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │ OpenAI API Format
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    LiteLLM API Server                        │
│  端口: 8000 (http://localhost:8000)                        │
│  - OpenAI 兼容接口 (/v1/chat/completions)                  │
│  - 模型代理 (GPT-4, Claude, 本地模型)                       │
│  - API Key 管理                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer (自定义)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ConversationManager (对话状态管理)                    │   │
│  │  - 对话历史存储                                         │   │
│  │  - 上下文窗口管理                                       │   │
│  │  - 意图识别                                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ToolRouter (工具路由和编排)                           │   │
│  │  - Function Calling 解析                               │   │
│  │  - 工具选择和执行                                       │   │
│  │  - 结果聚合                                             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Ecox Services Layer                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Financial    │ │ Data         │ │ Backtest     │        │
│  │ Analysis     │ │ Collection   │ │ Strategy     │        │
│  │ Service      │ │ Service      │ │ Engine       │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Real-time    │ │ Lazy         │ │ Validation   │        │
│  │ Market Data  │ │ Loading      │ │ Service      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  - PostgreSQL (财务数据、行情数据)                          │
│  - Redis (可选，用于对话历史缓存)                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心流程

```
1. Client → FastAPI: POST /v1/chat/completions
2. FastAPI → Agent: 调用 chat() 方法
3. Agent → ConversationManager: 提取上下文和实体
4. Agent → ToolRouter: 判断需要调用哪些工具
5. ToolRouter → Ecox Services: 执行工具
6. Ecox Services → ToolRouter: 返回结果
7. Agent → LLM: 生成最终回复
8. Agent → FastAPI: 返回 OpenAI 格式响应
9. FastAPI → Client: 返回给客户端
10. Agent → ConversationManager: 保存对话历史
```

---

## 3. 核心组件

### 3.1 目录结构

```
src/ecox/agent/
├── __init__.py
├── server.py                 # FastAPI 服务器启动
├── agent.py                 # 核心智能体类
├── conversation.py           # 对话管理器
├── tools/                   # 工具注册表
│   ├── __init__.py
│   ├── base.py             # 工具基类
│   ├── financial.py        # 财务分析工具
│   ├── market.py           # 行情查询工具
│   ├── backtest.py         # 回测工具
│   └── data.py             # 数据查询工具
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── message.py          # 消息模型
│   └── conversation.py     # 对话模型
├── exceptions.py            # 自定义异常
├── middleware.py            # 中间件和错误处理
└── utils/                   # 工具函数
    ├── __init__.py
    └── prompts.py          # 提示词模板

tests/agent/
├── __init__.py
├── test_agent.py            # Agent 核心测试
├── test_conversation.py     # 对话管理测试
├── test_tools/              # 工具测试
│   ├── test_financial.py
│   ├── test_market.py
│   └── test_backtest.py
├── test_api.py              # API 接口测试
└── fixtures/
    ├── test_data.py
    └── mock_services.py
```

### 3.2 组件详细设计

#### 3.2.1 LiteLLM 服务器 (`server.py`)

```python
"""LiteLLM API 服务器启动脚本"""
import os
import uvicorn
from litellm.proxy import ProxyServer

def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    model_list: list[str] = None
):
    """启动 LiteLLM API 服务器

    Args:
        host: 监听地址
        port: 监听端口
        model_list: 支持的模型列表
    """
    if model_list is None:
        model_list = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-sonnet-20241022"
        ]

    server = ProxyServer(
        host=host,
        port=port,
        model_list=model_list,
        api_keys=os.getenv("LITELLM_API_KEYS", "").split(","),
        master_key=os.getenv("LITELLM_MASTER_KEY")
    )

    uvicorn.run(
        app=server.app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
```

#### 3.2.2 核心智能体 (`agent.py`)

```python
"""Ecox AI 智能体核心类"""
import logging
import uuid
from typing import List, Optional, AsyncIterator
import httpx
from .conversation import ConversationManager
from .tools import ToolRouter
from .models import Message, Context
from .exceptions import ModelInvocationError, ToolExecutionError

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
        timeout: int = 30
    ):
        """初始化智能体

        Args:
            model: 默认使用的模型
            max_history: 最大历史消息数
            timeout: API 调用超时时间
        """
        self.model = model
        self.max_history = max_history
        self.timeout = timeout
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
            "财务": ["ROE", "毛利率", "净利润", "现金流", "资产"],
            "行情": ["股价", "涨跌幅", "成交量", "最新"],
            "回测": ["回测", "策略", "收益率"],
            "查询": ["查询", "数据", "SQL"]
        }

        content = " ".join([msg.content for msg in context.history])

        for category, terms in keywords.items():
            if any(term in content for term in terms):
                return True

        return False

    async def _execute_tools(self, context: Context) -> dict:
        """执行工具调用"""
        try:
            return await self.tool_router.execute(context)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise ToolExecutionError("tool_execution", str(e))

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

        # 添加工具结果（如果有）
        if tool_results:
            for tool_name, result in tool_results.items():
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False)
                })

        return messages

    async def _completion(self, messages: List[dict]) -> str:
        """调用模型生成回复"""
        try:
            # 调用 LiteLLM
            response = await self.client.post(
                "http://localhost:8000/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(f"Model invocation failed: {e}")
            raise ModelInvocationError(f"HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ModelInvocationError(str(e))
```

#### 3.2.3 对话管理器 (`conversation.py`)

```python
"""对话管理器"""
import logging
from typing import List, Optional
import re
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Session

from .models import Conversation, Message
from .database import get_db_session

logger = logging.getLogger(__name__)

class ConversationManager:
    """对话状态和历史管理"""

    def __init__(self, max_history: int = 20):
        """初始化对话管理器

        Args:
            max_history: 最大历史消息数
        """
        self.max_history = max_history

    async def get_context(
        self,
        messages: List[Message]
    ) -> Context:
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
            history=history,
            entities=entities,
            current_messages=messages
        )

    async def _load_history(self, session_id: str) -> List[Message]:
        """从数据库加载历史"""
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
        # 匹配：600809, SH600809, 中国平安
        stock_patterns = [
            r'\b[0-9]{6}\b',  # 6位数字
            r'\bSH[0-9]{6}\b',  # SH + 6位
            r'\bSZ[0-9]{6}\b',  # SZ + 6位
            r'[\u4e00-\u9fff]{2,4}',  # 中文名称（2-4字）
        ]

        for pattern in stock_patterns:
            matches = re.findall(pattern, content)
            entities.stock_codes.extend(matches)

        # 提取日期
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}年\d{1,2}季度',  # YYYY年Q季度
            r'\d{4}半年报',  # YYYY半年报
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            entities.dates.extend(matches)

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

            conv.updated_at = datetime.now()

            session.commit()
```

#### 3.2.4 工具系统 (`tools/`)

```python
"""工具基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """工具基类"""

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
            "properties": {}
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


"""财务分析工具"""
from ...services.financial_analysis_service import FinancialAnalysisService

class FinancialAnalysisTool(Tool):
    """财务分析工具"""

    @property
    def name(self) -> str:
        return "financial_analysis"

    @property
    def description(self) -> str:
        return "分析股票财务数据，包括ROE、杜邦分析、现金流等"

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
                    "description": "分析模块列表（profitability, cash_flow, solvency等）"
                }
            },
            "required": ["stock_code"]
        }

    async def execute(self, stock_code: str, modules: List[str] = None) -> Dict:
        """执行财务分析"""
        from ...utils import code_format

        service = FinancialAnalysisService()
        result = await service.calculate_metrics(
            stock_code=code_format(stock_code),
            modules=modules
        )
        return result


"""工具路由器"""
from typing import List
from .financial import FinancialAnalysisTool
from .market import MarketDataTool
from .backtest import BacktestTool
from .data import DataQueryTool

class ToolRouter:
    """工具路由和编排"""

    def __init__(self):
        self.tools = {
            "financial_analysis": FinancialAnalysisTool(),
            "market_data": MarketDataTool(),
            "backtest": BacktestTool(),
            "data_query": DataQueryTool(),
        }

    async def execute(self, context: Context) -> Dict[str, Any]:
        """根据上下文执行工具

        Args:
            context: 对话上下文

        Returns:
            工具执行结果字典
        """
        # 根据实体和内容判断需要调用的工具
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

    def _select_tools(self, context: Context) -> List[str]:
        """根据上下文选择工具"""
        tools = []

        # 有股票代码实体
        if context.entities.stock_codes:
            tools.append("financial_analysis")
            tools.append("market_data")

        # 有日期实体
        if context.entities.dates:
            tools.append("data_query")

        # 包含特定关键词
        content = " ".join([msg.content for msg in context.current_messages])

        if "回测" in content or "策略" in content:
            tools.append("backtest")

        if "查询" in content or "SQL" in content:
            tools.append("data_query")

        return tools

    def _prepare_args(self, tool: Tool, context: Context) -> Dict:
        """准备工具参数"""
        if tool.name == "financial_analysis":
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None,
                "modules": ["profitability", "solvency"]  # 默认模块
            }

        # 其他工具的参数准备逻辑...

        return {}
```

---

## 4. API 接口设计

### 4.1 OpenAI 兼容接口

```python
"""FastAPI 应用"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Literal
import httpx
import json

app = FastAPI(
    title="Ecox AI API",
    description="A股投资智能体 API",
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
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
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

# 核心 API 端点
@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """OpenAI 兼容的聊天接口

    这是与 OpenAI Chat Completions API 完全兼容的接口。
    支持：
    - 多轮对话
    - 流式输出
    - Function Calling (工具调用)
    """
    agent = EcoxA(model=request.model)

    try:
        if request.stream:
            # 流式响应
            return StreamingResponse(
                agent.chat_stream(request.messages),
                media_type="text/event-stream"
            )
        else:
            # 普通响应
            response_content = await agent.chat(request.messages)

            return ChatResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                usage=ChatUsage(
                    prompt_tokens=estimate_tokens(request.messages),
                    completion_tokens=estimate_tokens([response_content]),
                    total_tokens=estimate_tokens(request.messages) + estimate_tokens([response_content])
                )
            )

    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
                "id": "claude-3-sonnet-20241022",
                "object": "model",
                "owned_by": "ecox"
            }
        ]
    }
```

### 4.2 数据流

详见第二部分的架构图和核心流程。

---

## 5. 错误处理

### 5.1 异常定义

```python
"""自定义异常"""
class AgentException(Exception):
    """Agent 基础异常"""
    pass

class ToolExecutionError(AgentException):
    """工具执行错误"""
    def __init__(self, tool_name: str, error: str):
        self.tool_name = tool_name
        self.error = error
        super().__init__(f"Tool {tool_name} failed: {error}")

class ConversationError(AgentException):
    """对话管理错误"""
    pass

class ModelInvocationError(AgentException):
    """模型调用错误"""
    pass
```

### 5.2 全局异常处理

```python
"""全局异常处理器"""
@app.exception_handler(AgentException)
async def agent_exception_handler(request: Request, exc: AgentException):
    """所有 Agent 异常的统一处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": str(exc),
                "type": exc.__class__.__name__
            }
        }
    )

@app.exception_handler(httpx.HTTPError)
async def http_error_handler(request: Request, exc: httpx.HTTPError):
    """HTTP 错误处理"""
    return JSONResponse(
        status_code=exc.response.status_code,
        content={
            "error": {
                "message": "External service error",
                "type": "http_error",
                "details": exc.response.text
            }
        }
    )
```

### 5.3 重试和降级策略

详见第三部分核心智能体的 `_execute_tool_with_retry` 方法。

---

## 6. 测试策略

### 6.1 测试目录结构

```
tests/agent/
├── conftest.py              # pytest 配置和 fixture
├── test_agent.py            # Agent 核心测试
├── test_conversation.py     # 对话管理测试
├── test_tools/              # 工具测试
│   ├── test_financial.py
│   ├── test_market.py
│   └── test_backtest.py
├── test_api.py              # API 接口测试
├── test_integration.py      # 集成测试
└── fixtures/
    ├── test_data.py         # 测试数据
    └── mock_services.py     # Mock 服务
```

### 6.2 关键测试用例

详见第二部分错误处理和测试章节。

---

## 7. 部署

### 7.1 环境要求

- Python 3.13+
- PostgreSQL（用于对话历史）
- LiteLLM（已安装）
- Ecox 项目依赖

### 7.2 启动步骤

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量
export LITELLM_API_KEYS="sk-xxx,sk-claude-xxx"
export LITELLM_MASTER_KEY="litellm-master-key"

# 3. 启动 LiteLLM 代理（新终端）
uv run litellm-proxy --model_list gpt-4,gpt-4-turbo,claude-3-sonnet-20241022

# 4. 启动 Ecox AI 服务（原终端）
uv run python -m ecox.agent.server
```

### 7.3 使用示例

```bash
# 测试 API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "中国平安的ROE是多少？"}
    ]
  }'

# 使用 OpenAI Python SDK
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # 本地服务不需要真实 key
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": "中国平安的ROE是多少？"
    }]
)

print(response.choices[0].message.content)
```

---

## 8. 后续优化

### 8.1 Phase 2 功能（可选）

1. **流式输出优化** - 实现真正的 SSE 流式响应
2. **多模型支持** - 支持本地模型（Ollama、vLLM）
3. **工具增强** - 添加更多工具（如技术分析、新闻分析）
4. **对话优化** - 添加记忆持久化、用户画像
5. **前端界面** - 提供简单的 Web UI

### 8.2 监控和日志

- 对话日志记录
- 工具调用统计
- 性能监控
- 错误追踪

---

**文档版本**: 1.0
**创建日期**: 2026-03-17
**状态**: 待实施
