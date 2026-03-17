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
    meta_data = Column("metadata", JSON, nullable=True)
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
        self.meta_data = metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Expose metadata as a runtime attribute
        self.__dict__['metadata'] = metadata
