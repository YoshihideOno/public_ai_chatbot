from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any


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
