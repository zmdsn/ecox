"""FastAPI 服务器"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from .agent import EcoxA
from .models.message import Message

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ecox AI Agent API",
    description="A股投资分析智能体 API",
    version="1.0.0"
)

# 初始化智能体
agent = EcoxA()


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-4"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    object: str = "model"
    created: int
    owned_by: str


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ecox-ai-agent",
        "version": "1.0.0"
    }


@app.get("/v1/models")
async def list_models():
    """列出可用模型"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1677610602,
                "owned_by": "ecox"
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "ecox"
            }
        ]
    }


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """OpenAI 兼容的聊天完成端点"""
    import time
    import uuid

    try:
        # 转换消息格式
        messages = [
            Message(role=msg.role, content=msg.content)
            for msg in request.messages
        ]

        # 调用智能体
        response_content = await agent.chat(messages, stream=request.stream)

        # 构建OpenAI格式响应
        response = ChatResponse(
            id=str(uuid.uuid4()),
            created=int(time.time()),
            model=request.model or "gpt-4",
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": sum(len(msg.content.split()) for msg in messages),
                "completion_tokens": len(response_content.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in messages) + len(response_content.split())
            }
        )

        return response

    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Ecox AI Agent API",
        "docs": "/docs",
        "health": "/health",
        "chat": "/v1/chat/completions"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
