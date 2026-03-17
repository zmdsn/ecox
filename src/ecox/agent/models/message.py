"""消息数据模型"""
from datetime import datetime
from typing import Optional, ClassVar
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
    session_id: ClassVar[Optional[str]] = None
    tool_calls: ClassVar[Optional[list]] = None
    tool_call_id: ClassVar[Optional[str]] = None

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
