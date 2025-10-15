from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.models.chat import Chat, Message
from app.schemas.chat import ChatCreate, ChatUpdate, MessageCreate


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_chats(self, user_id: int) -> List[Chat]:
        """Get all chats for a user"""
        result = await self.db.execute(
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
        )
        return result.scalars().all()

    async def get_chat_with_messages(self, chat_id: int, user_id: int) -> Optional[Chat]:
        """Get a chat with all its messages"""
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.messages))
            .where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_chat(self, user_id: int, chat_data: ChatCreate) -> Chat:
        """Create a new chat"""
        db_chat = Chat(
            user_id=user_id,
            title=chat_data.title,
        )
        self.db.add(db_chat)
        await self.db.commit()
        await self.db.refresh(db_chat)
        return db_chat

    async def update_chat(self, chat_id: int, user_id: int, chat_update: ChatUpdate) -> Optional[Chat]:
        """Update a chat"""
        chat = await self.get_chat_with_messages(chat_id, user_id)
        if not chat:
            return None

        update_data = chat_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chat, field, value)

        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def delete_chat(self, chat_id: int, user_id: int) -> bool:
        """Delete a chat"""
        chat = await self.get_chat_with_messages(chat_id, user_id)
        if not chat:
            return False

        await self.db.delete(chat)
        await self.db.commit()
        return True

    async def add_message(self, chat_id: int, user_id: int, message_data: MessageCreate) -> Optional[Message]:
        """Add a message to a chat"""
        # Verify chat exists and belongs to user
        chat = await self.get_chat_with_messages(chat_id, user_id)
        if not chat:
            return None

        db_message = Message(
            chat_id=chat_id,
            role=message_data.role,
            content=message_data.content,
        )
        self.db.add(db_message)
        await self.db.commit()
        await self.db.refresh(db_message)
        return db_message
