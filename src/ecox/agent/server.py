"""FastAPI 服务器"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
import uuid
import time

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
                "id": "ecox",
                "object": "model",
                "created": 1677610602,
                "owned_by": "ecox"
            },
            {
                "id": "qwen3-code",
                "object": "model",
                "created": 1677610602,
                "owned_by": "ecox"
            },
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


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI 兼容的聊天完成端点（支持流式和非流式）"""

    # 转换消息格式
    messages = [
        Message(role=msg.role, content=msg.content)
        for msg in request.messages
    ]

    # 流式响应
    if request.stream:
        return await _stream_chat_completion(request, messages)

    # 非流式响应
    return await _nonstream_chat_completion(request, messages)


async def _nonstream_chat_completion(request: ChatRequest, messages: List[Message]) -> ChatResponse:
    """非流式聊天完成"""
    try:
        # 调用智能体
        response_content = await agent.chat(messages, stream=False)

        # 确保是字符串
        if hasattr(response_content, '__aiter__'):
            # 如果是生成器，收集所有内容
            chunks = []
            async for chunk in response_content:
                chunks.append(chunk)
            response_content = ''.join(chunks)

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


async def _stream_chat_completion(request: ChatRequest, messages: List[Message]):
    """流式聊天完成"""
    try:
        # 生成唯一 ID
        completion_id = str(uuid.uuid4())
        created_time = int(time.time())
        model_name = request.model or "gpt-4"

        # 调用智能体获取流式响应
        response_stream = await agent.chat(messages, stream=True)

        async def generate():
            """生成 SSE 格式的流式响应"""
            try:
                # response_stream 应该是一个异步生成器
                async for chunk in response_stream:
                    if chunk:
                        yield f"data: {json.dumps(_create_sse_chunk(completion_id, created_time, model_name, chunk), ensure_ascii=False)}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Stream generation error: {e}", exc_info=True)
                error_chunk = f"\n\n[错误: {str(e)}]"
                yield f"data: {json.dumps(_create_sse_chunk(completion_id, created_time, model_name, error_chunk), ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Stream chat completion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _create_sse_chunk(completion_id: str, created: int, model: str, content: str) -> dict:
    """创建 SSE 数据块"""
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {
                "content": content
            },
            "finish_reason": None
        }]
    }


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
