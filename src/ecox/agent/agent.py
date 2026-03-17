"""Ecox AI 智能体"""
import logging
from typing import List, Optional, Dict, Any
from .models.message import Message
from .models.context import Context
from .conversation import ConversationManager
from .tools.router import ToolRouter
from .utils.prompts import SYSTEM_PROMPT
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class EcoxA:
    """Ecox AI 智能体核心类"""

    def __init__(
        self,
        model: str = "gpt-4",
        max_history: int = 10,
        timeout: float = 30.0,
        litellm_base_url: str = "http://localhost:4000"
    ):
        """初始化智能体

        Args:
            model: 使用的模型名称
            max_history: 最大历史消息数
            timeout: 请求超时时间
            litellm_base_url: LiteLLM API地址
        """
        self.model = model
        self.max_history = max_history
        self.timeout = timeout
        self.litellm_base_url = litellm_base_url

        self.conversation_manager = ConversationManager(max_history=max_history)
        self.tool_router = ToolRouter()

    async def chat(self, messages: List[Message], stream: bool = False) -> str:
        """主对话方法

        Args:
            messages: 用户消息列表
            stream: 是否使用流式响应

        Returns:
            AI响应内容
        """
        # 获取上下文
        context = self.conversation_manager.get_context(messages)

        # 判断是否需要工具
        if self._needs_tools(context):
            # 执行工具
            tool_results = await self._execute_tools(context)

            # 使用工具结果生成回复
            response = await self._generate_with_tools(messages, tool_results)
        else:
            # 直接生成回复
            response = await self._generate_direct(messages)

        # 保存对话
        session_id = messages[0].session_id or f"session_{datetime.now().timestamp()}"
        self.conversation_manager.save(session_id, messages, response)

        return response

    def _needs_tools(self, context: Context) -> bool:
        """判断是否需要调用工具

        Args:
            context: 对话上下文

        Returns:
            是否需要工具
        """
        # 有实体时需要工具
        if context.entities.stock_codes or context.entities.dates:
            return True

        # 检查关键词
        content = " ".join([msg.content for msg in context.current_messages])
        keywords = ["分析", "查询", "回测", "策略", "财务", "行情", "股价"]
        return any(keyword in content for keyword in keywords)

    async def _execute_tools(self, context: Context) -> Dict[str, Any]:
        """执行工具调用

        Args:
            context: 对话上下文

        Returns:
            工具执行结果
        """
        return await self.tool_router.execute(context)

    async def _generate_with_tools(
        self,
        messages: List[Message],
        tool_results: Dict[str, Any]
    ) -> str:
        """使用工具结果生成回复

        Args:
            messages: 用户消息
            tool_results: 工具执行结果

        Returns:
            AI回复
        """
        # 构建消息
        api_messages = self._build_messages(messages, tool_results=tool_results)

        # 调用API
        response = await self._completion(api_messages)

        return response

    async def _generate_direct(self, messages: List[Message]) -> str:
        """直接生成回复（不使用工具）

        Args:
            messages: 用户消息

        Returns:
            AI回复
        """
        # 构建消息
        api_messages = self._build_messages(messages)

        # 调用API
        response = await self._completion(api_messages)

        return response

    def _build_messages(
        self,
        messages: List[Message],
        tool_results: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """构建API消息列表

        Args:
            messages: 用户消息
            tool_results: 工具执行结果（可选）

        Returns:
            API消息列表
        """
        api_messages = []

        # 添加系统提示
        api_messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        })

        # 添加工具结果
        if tool_results:
            tool_summary = "\n\n## 工具执行结果\n\n"
            for tool_name, result in tool_results.items():
                if "error" not in result:
                    tool_summary += f"**{tool_name}**:\n{result}\n\n"
                else:
                    tool_summary += f"**{tool_name}**: {result['error']}\n\n"

            api_messages.append({
                "role": "system",
                "content": tool_summary
            })

        # 添加用户消息
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return api_messages

    async def _completion(self, messages: List[Dict[str, str]]) -> str:
        """调用LLM API

        Args:
            messages: 消息列表

        Returns:
            AI回复内容
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.litellm_base_url}/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7
                    }
                )

                response.raise_for_status()
                data = response.json()

                return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return f"抱歉，我遇到了一些问题：{str(e)}"
