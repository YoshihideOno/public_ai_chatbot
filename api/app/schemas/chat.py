from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
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


class ChatRequest(BaseModel):
    """RAGチャットリクエスト"""
    query: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    top_k: Optional[int] = None
    session_id: Optional[str] = None
    temperature: Optional[float] = None
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < 0.0 or v > 2.0):
            raise ValueError('temperatureは0.0-2.0の範囲である必要があります')
        return v


class ChatResponse(BaseModel):
    """RAGチャットレスポンス"""
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: str
    metadata: Dict[str, Any]
