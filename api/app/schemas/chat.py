from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    chat_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatBase(BaseModel):
    title: Optional[str] = None


class ChatCreate(ChatBase):
    pass


class ChatUpdate(BaseModel):
    title: Optional[str] = None


class Chat(ChatBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[Message] = []

    class Config:
        from_attributes = True


class ChatWithMessages(Chat):
    messages: List[Message] = []
