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
    created_at = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), nullable=False)

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

        # Create metadata as a runtime attribute using descriptor protocol
        # This bypasses SQLAlchemy's attribute instrumentation
        object.__setattr__(self, 'metadata', metadata)

    # Use a custom descriptor for metadata access
    class _MetadataDescriptor:
        """Descriptor to provide metadata access that maps to meta_data."""

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            return object.__getattribute__(obj, 'meta_data')

        def __set__(self, obj, value):
            object.__setattr__(obj, 'meta_data', value)


# Attach the metadata descriptor to the class after definition
Conversation.metadata = Conversation._MetadataDescriptor()
