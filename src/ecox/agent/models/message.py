"""Message ORM model for agent conversations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Message(Base):
    """Message model for storing conversation messages.

    Attributes:
        id: Primary key
        conversation_id: Foreign key to conversations table
        role: Message role (user/assistant/system/tool)
        content: Message content
        created_at: Timestamp when message was created

    Runtime Attributes (not persisted):
        session_id: Optional session identifier
        tool_calls: Optional list of tool calls made
        tool_call_id: Optional tool call identifier
    """

    __tablename__ = "agent_messages"

    VALID_ROLES = {"user", "assistant", "system", "tool"}

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("agent_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(
        self,
        conversation_id: int,
        role: str,
        content: str,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a Message instance.

        Args:
            conversation_id: ID of the conversation this message belongs to
            role: Message role (must be one of VALID_ROLES)
            content: Message content
            id: Optional specific ID (for testing/migration)
            created_at: Optional creation timestamp

        Raises:
            ValueError: If role is not in VALID_ROLES
        """
        if role not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of {self.VALID_ROLES}"
            )

        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        if id is not None:
            self.id = id
        if created_at is not None:
            self.created_at = created_at

        # Runtime attributes (not persisted to database)
        # These are set directly on instances, not as class attributes
        # to avoid SQLAlchemy tracking them as columns

    def __repr__(self) -> str:
        """Return string representation of Message."""
        return (
            f"<Message(id={self.id}, conversation_id={self.conversation_id}, "
            f"role='{self.role}', content='{self.content[:50]}...')>"
        )
