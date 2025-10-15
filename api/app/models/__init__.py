# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .chat import Chat, Message

# Update User model to include relationship
from sqlalchemy.orm import relationship
User.chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

__all__ = ["User", "Chat", "Message"]
