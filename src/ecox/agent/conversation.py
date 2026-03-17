"""对话管理器"""
import re
import logging
from typing import List, Optional
from .models.context import Context, Entities
from .models.message import Message
from ecox.agent.models.conversation import Conversation
from ecox.database import get_db_session
from ecox import models

logger = logging.getLogger(__name__)


class ConversationManager:
    """对话上下文管理器"""

    def __init__(self, max_history: int = 10):
        """初始化对话管理器

        Args:
            max_history: 最大历史消息数量
        """
        self.max_history = max_history

    def get_context(self, messages: List[Message]) -> Context:
        """获取对话上下文

        Args:
            messages: 当前消息列表

        Returns:
            对话上下文对象
        """
        if not messages:
            return Context(session_id="")

        session_id = messages[0].session_id or ""

        # 加载历史
        history = self._load_history(session_id) if session_id else []

        # 提取实体
        entities = self._extract_entities(messages)

        return Context(
            session_id=session_id,
            history=history,
            entities=entities,
            current_messages=messages
        )

    def _load_history(self, session_id: str) -> List[Message]:
        """加载历史消息"""
        try:
            with get_db_session() as session:
                conv = session.query(Conversation).filter(
                    Conversation.session_id == session_id
                ).first()

                if not conv:
                    return []

                # 转换为Message对象
                history = [
                    Message(
                        role=msg.role,
                        content=msg.content,
                        id=msg.id,
                        conversation_id=msg.conversation_id
                    )
                    for msg in conv.messages[-self.max_history:]
                ]

                return history

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def _extract_entities(self, messages: List[Message]) -> Entities:
        """从消息中提取实体

        Args:
            messages: 消息列表

        Returns:
            提取的实体对象
        """
        entities = Entities()

        # 合并所有消息内容
        content = " ".join([msg.content for msg in messages])

        # 提取股票代码（6位数字，可能带SH/SZ前缀）
        stock_pattern = r'[0-6]\d{5}|\bSH\d{6}\b|\bSZ\d{6}\b'
        entities.stock_codes = list(set(re.findall(stock_pattern, content)))

        # 提取日期（多种格式）
        date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?|\d{4}Q[1-4]'
        entities.dates = list(set(re.findall(date_pattern, content)))

        # 提取公司名（常见A股公司）
        # 这里简化处理，实际可以使用NER模型
        common_companies = [
            "中国平安", "贵州茅台", "招商银行", "五粮液", "腾讯控股",
            "阿里巴巴", "比亚迪", "宁德时代", "工商银行", "建设银行"
        ]
        for company in common_companies:
            if company in content:
                entities.company_names.append(company)

        entities.company_names = list(set(entities.company_names))

        return entities

    def save(self, session_id: str, messages: List[Message], response: str):
        """保存对话到数据库

        Args:
            session_id: 会话ID
            messages: 用户消息列表
            response: AI响应
        """
        try:
            with get_db_session() as session:
                # 获取或创建对话
                conv = session.query(Conversation).filter(
                    Conversation.session_id == session_id
                ).first()

                if not conv:
                    conv = Conversation(session_id=session_id)
                    session.add(conv)
                    session.flush()

                # 保存用户消息
                for msg in messages:
                    db_msg = models.Message(
                        conversation_id=conv.id,
                        role=msg.role,
                        content=msg.content
                    )
                    session.add(db_msg)

                # 保存AI响应
                response_msg = models.Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=response
                )
                session.add(response_msg)

                session.commit()

        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
