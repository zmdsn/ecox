"""Conversation ORM model for agent conversations."""

from datetime import datetime
from typing import Optional, Any, Dict

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship

from .message import Base


class Conversation(Base):
    """Conversation model for storing agent conversation sessions.

    Attributes:
        id: Primary key
        session_id: Unique session identifier
        metadata: Additional metadata as JSON
        created_at: Timestamp when conversation was created
        updated_at: Timestamp when conversation was last updated
        messages: Relationship to Message objects
    """

    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan")

    def __init__(
        self,
        session_id: str,
        meta_data: Optional[Dict[str, Any]] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a Conversation instance.

        Args:
            session_id: Unique session identifier
            meta_data: Optional metadata dictionary
            id: Optional specific ID (for testing/migration)
            created_at: Optional creation timestamp
            updated_at: Optional update timestamp
        """
        self.session_id = session_id
        self.meta_data = meta_data
        if id is not None:
            self.id = id
        if created_at is not None:
            self.created_at = created_at
        if updated_at is not None:
            self.updated_at = updated_at

    def __repr__(self) -> str:
        """Return string representation of Conversation."""
        return (
            f"<Conversation(id={self.id}, session_id='{self.session_id}', "
            f"messages_count={len(self.messages)})>"
        )
