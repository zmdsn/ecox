# Ecox AI Agent 使用指南

## 概述

Ecox AI Agent 是一个专业的 A 股投资分析智能体，通过工具调用能力提供财务分析、行情数据查询、数据检索和策略回测功能。

## 核心特性

1. **多工具集成**：财务分析、行情查询、数据检索、策略回测
2. **智能路由**：自动根据对话上下文选择合适的工具
3. **对话记忆**：持久化存储对话历史
4. **OpenAI 兼容**：标准 API 格式，易于集成
5. **中文优化**：针对 A 股投资分析场景优化

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 创建 Agent 相关数据库表
uv run python scripts/init_agent_tables.py
```

### 3. 启动 LiteLLM 代理

```bash
# 启动 LiteLLM 代理（端口 4000）
uv run python scripts/start_litellm_proxy.py
```

### 4. 启动 Agent 服务器

```bash
# 启动 FastAPI 服务器（端口 8000）
uv run python scripts/start_agent_server.py --port 8000
```

### 5. 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 聊天测试
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "分析中国平安601318的财务状况"}
    ]
  }'
```

## 使用示例

### Python 客户端

```python
import asyncio
from ecox.agent import EcoxA
from ecox.agent.models.message import Message

async def main():
    # 初始化智能体
    agent = EcoxA(model="gpt-4")

    # 发送消息
    messages = [
        Message(role="user", content="分析中国平安601318的财务状况", session_id="demo-1")
    ]

    response = await agent.chat(messages)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### cURL 示例

```bash
# 财务分析
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "分析贵州茅台600519的ROE"}
    ]
  }'

# 行情查询
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "查询比亚迪002594的最新股价"}
    ]
  }'

# 策略回测
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "对中国平安进行双均线策略回测，2023年到2024年"}
    ]
  }'
```

## API 端点

### POST /v1/chat/completions

OpenAI 兼容的聊天完成端点。

**请求格式：**
```json
{
  "messages": [
    {"role": "user", "content": "分析601318"}
  ],
  "model": "gpt-4",
  "temperature": 0.7,
  "stream": false
}
```

**响应格式：**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "分析结果..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

### GET /health

健康检查端点。

**响应：**
```json
{
  "status": "healthy",
  "service": "ecox-ai-agent",
  "version": "1.0.0"
}
```

### GET /v1/models

列出可用模型。

**响应：**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1677610602,
      "owned_by": "ecox"
    }
  ]
}
```

## 工具说明

### 1. 财务分析工具 (financial_analysis)

**功能**：分析股票财务指标（ROE、毛利率、现金流等）

**触发关键词**：财务、分析、ROE、毛利率、现金流

**参数**：
- `stock_code` (必需)：股票代码
- `modules` (可选)：分析模块列表
- `report_date` (可选)：报告日期

### 2. 行情数据工具 (market_data)

**功能**：查询股票实时行情数据

**触发关键词**：行情、股价、最新价格、涨跌幅

**参数**：
- `stock_code` (必需)：股票代码

### 3. 数据查询工具 (data_query)

**功能**：执行 SQL 查询获取历史数据

**触发关键词**：查询、SQL、历史数据

**参数**：
- `sql` (必需)：SQL 查询语句（仅支持 SELECT）

### 4. 策略回测工具 (backtest)

**功能**：对股票进行策略回测

**触发关键词**：回测、策略、双均线、MACD

**参数**：
- `stock_code` (必需)：股票代码
- `strategy` (可选)：策略名称
- `start_date` (必需)：开始日期
- `end_date` (必需)：结束日期
- `initial_cash` (可选)：初始资金

## 常见问题

### Q: 如何添加自定义工具？

A: 继承 `Tool` 基类并实现抽象方法：

```python
from ecox.agent.tools.base import Tool

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "我的自定义工具"

    async def execute(self, **kwargs):
        # 实现工具逻辑
        return {"result": "success"}
```

### Q: 如何修改模型配置？

A: 编辑 `litellm_config.yaml` 文件，添加或修改模型配置。

### Q: 如何查看对话历史？

A: 对话历史存储在 `agent_conversations` 和 `agent_messages` 表中，可以直接查询数据库。

### Q: 支持哪些 LLM 提供商？

A: 通过 LiteLLM 支持 OpenAI、Anthropic、阿里云通义千问等多个提供商。

### Q: 如何调试工具调用？

A: 设置环境变量 `LOGLEVEL=DEBUG` 可以查看详细的工具调用日志。

## 高级配置

### 环境变量

```bash
# LLM API 配置
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"

# 数据库配置
export PG_HOST="localhost"
export PG_PORT="5432"
export PG_USER="your-user"
export PG_PASSWORD="your-password"
export PG_DATABASE="stock"

# Agent 配置
export AGENT_MODEL="gpt-4"
export AGENT_MAX_HISTORY="10"
export AGENT_TIMEOUT="30.0"
export LITELLM_BASE_URL="http://localhost:4000"
```

### 服务器配置

```bash
# 启动参数
uv run python scripts/start_agent_server.py \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4  # 生产环境使用多进程
```

## 性能优化

1. **连接池**：数据库使用连接池提高并发性能
2. **异步执行**：所有工具调用都是异步的，不会阻塞
3. **缓存**：可以考虑添加 Redis 缓存常用查询结果
4. **负载均衡**：生产环境可以使用多个工作进程

## 安全建议

1. **API 密钥**：使用环境变量存储，不要提交到代码仓库
2. **SQL 注入**：数据查询工具只允许 SELECT 语句
3. **访问控制**：生产环境建议添加 API 认证
4. **日志脱敏**：确保日志中不包含敏感信息

## 技术支持

如有问题，请查阅：
- 项目文档：`docs/`
- API 文档：`http://localhost:8000/docs`
- 源代码：`src/ecox/agent/`
