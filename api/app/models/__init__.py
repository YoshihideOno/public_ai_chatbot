# Import all models to ensure they are registered with SQLAlchemy
# Import in dependency order to avoid foreign key issues
from .tenant import Tenant
from .user import User
from .file import File
from .chunk import Chunk
from .chat import Chat, Message
from .verification_token import VerificationToken

# Update User model to include relationship
from sqlalchemy.orm import relationship
User.chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

__all__ = ["Tenant", "User", "File", "Chunk", "Chat", "Message", "VerificationToken"]
