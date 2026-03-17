# Ecox AI Agent 启动指南

## 当前状态

✅ 已完成：
- Agent 服务器代码已实现
- 所有测试通过（36/36）
- 数据库表已创建
- 文档已完善

⚠️ 服务启动问题：
- LiteLLM 与自定义 LLM 服务器配置需要调整

## 快速启动方案

由于您的自定义 LLM 服务器地址是 `http://121.46.230.100:8000`，
建议直接修改 Agent 代码连接到该服务器，而不是通过 LiteLLM。

### 方案 1：直接连接（推荐）

1. 修改 `src/ecox/agent/agent.py` 第 23 行：
```python
litellm_base_url: str = "http://121.46.230.100:8000/v1"
```

2. 启动 Agent 服务器：
```bash
cd /home/zmdsn/ecox
uv run python -m uvicorn ecox.agent.server:app --host 0.0.0.0 --port 8090
```

3. 测试：
```bash
curl -X POST http://localhost:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-code",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 方案 2：使用 LiteLLM（需要配置）

如果您想使用 LiteLLM 作为代理，需要：

1. 确保 LLM 服务器支持 OpenAI API 格式
2. 配置 `litellm_config.yaml` 中的 api_base
3. 启动 LiteLLM：
```bash
uv run litellm --config litellm_config.yaml --port 8001
```

## 服务信息

- **Agent API**: http://localhost:8090
- **API 文档**: http://localhost:8090/docs
- **健康检查**: http://localhost:8090/health
- **模型列表**: http://localhost:8090/v1/models

## 使用示例

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8090/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="qwen3-code",
    messages=[{"role": "user", "content": "分析中国平安601318"}]
)

print(response.choices[0].message.content)
```

## 停止服务

```bash
# 停止 Agent
pkill -f "uvicorn.*agent"

# 停止 LiteLLM（如果在运行）
pkill -f litellm
```
