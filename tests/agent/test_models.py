"""Tests for agent data models."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ecox.agent.models import Message, Conversation, Base


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestMessage:
    """Test Message model."""

    def test_message_creation(self, db_session):
        """Test creating a message with valid data."""
        conversation = Conversation(session_id="test-session-1")
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hello, how are you?"
        )
        db_session.add(message)
        db_session.commit()

        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.created_at is not None

    def test_message_with_id(self, db_session):
        """Test creating a message with specific ID."""
        conversation = Conversation(session_id="test-session-2")
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            id=999,
            conversation_id=conversation.id,
            role="assistant",
            content="I'm doing well, thank you!"
        )
        db_session.add(message)
        db_session.commit()

        assert message.id == 999

    def test_message_invalid_role(self, db_session):
        """Test that creating a message with invalid role raises ValueError."""
        conversation = Conversation(session_id="test-session-3")
        db_session.add(conversation)
        db_session.commit()

        with pytest.raises(ValueError, match="Invalid role"):
            Message(
                conversation_id=conversation.id,
                role="invalid_role",
                content="This should fail"
            )

    def test_message_all_valid_roles(self, db_session):
        """Test that all valid roles work."""
        conversation = Conversation(session_id="test-session-4")
        db_session.add(conversation)
        db_session.commit()

        valid_roles = ["user", "assistant", "system", "tool"]
        for role in valid_roles:
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=f"Message with role {role}"
            )
            db_session.add(message)
            db_session.commit()

            assert message.role == role

    def test_message_runtime_attributes(self, db_session):
        """Test runtime attributes that can be set on instances."""
        conversation = Conversation(session_id="test-session-5")
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Test message"
        )

        # Test that runtime attributes can be set
        message.session_id = "runtime-session-123"
        message.tool_calls = [{"name": "test_tool", "args": {}}]
        message.tool_call_id = "call_123"

        assert message.session_id == "runtime-session-123"
        assert message.tool_calls == [{"name": "test_tool", "args": {}}]
        assert message.tool_call_id == "call_123"

        # Persist to database
        db_session.add(message)
        db_session.commit()

        # Retrieve from database - runtime attributes should be retrievable on the instance
        retrieved = db_session.query(Message).filter_by(id=message.id).first()
        # Note: SQLAlchemy may persist instance attributes, but they are not defined as columns
        # The important thing is that they can be set and used at runtime


class TestConversation:
    """Test Conversation model."""

    def test_conversation_creation(self, db_session):
        """Test creating a conversation."""
        conversation = Conversation(session_id="test-conversation-1")
        db_session.add(conversation)
        db_session.commit()

        assert conversation.id is not None
        assert conversation.session_id == "test-conversation-1"
        assert conversation.meta_data is None  # Default value
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    def test_conversation_with_metadata(self, db_session):
        """Test creating a conversation with metadata."""
        metadata = {"user_name": "Alice", "theme": "dark"}
        conversation = Conversation(
            session_id="test-conversation-2",
            meta_data=metadata
        )
        db_session.add(conversation)
        db_session.commit()

        assert conversation.meta_data == metadata

    def test_conversation_with_messages(self, db_session):
        """Test conversation with multiple messages."""
        conversation = Conversation(session_id="test-conversation-3")
        db_session.add(conversation)
        db_session.commit()

        # Add messages
        message1 = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hello"
        )
        message2 = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Hi there!"
        )
        db_session.add_all([message1, message2])
        db_session.commit()

        # Test relationship
        assert len(conversation.messages) == 2
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[1].content == "Hi there!"

    def test_conversation_unique_session_id(self, db_session):
        """Test that session_id must be unique."""
        conversation1 = Conversation(session_id="duplicate-session")
        db_session.add(conversation1)
        db_session.commit()

        conversation2 = Conversation(session_id="duplicate-session")
        db_session.add(conversation2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_conversation_backref(self, db_session):
        """Test that message has conversation backref."""
        conversation = Conversation(session_id="test-conversation-4")
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Test backref"
        )
        db_session.add(message)
        db_session.commit()

        assert message.conversation == conversation
        assert message.conversation.session_id == "test-conversation-4"
