from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.chat import Chat, ChatCreate, ChatUpdate, ChatWithMessages, Message, MessageCreate, ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.rag_pipeline import RAGPipeline
from app.api.v1.deps import get_current_user
from app.schemas.user import User

router = APIRouter()


@router.get("/", response_model=List[Chat])
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chats for current user"""
    chat_service = ChatService(db)
    chats = await chat_service.get_user_chats(current_user.id)
    return chats


@router.post("/", response_model=Chat)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat"""
    chat_service = ChatService(db)
    chat = await chat_service.create_chat(current_user.id, chat_data)
    return chat


@router.get("/{chat_id}", response_model=ChatWithMessages)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat with messages"""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat_with_messages(chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return chat


@router.put("/{chat_id}", response_model=Chat)
async def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat"""
    chat_service = ChatService(db)
    chat = await chat_service.update_chat(chat_id, current_user.id, chat_update)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return chat


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat"""
    chat_service = ChatService(db)
    success = await chat_service.delete_chat(chat_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"message": "Chat deleted successfully"}


@router.post("/{chat_id}/messages", response_model=Message)
async def create_message(
    chat_id: int,
    message_data: MessageCreate,
    model: Optional[str] = Query(None, description="使用するLLMモデル"),
    max_tokens: Optional[int] = Query(None, description="最大トークン数"),
    temperature: Optional[float] = Query(None, description="温度パラメータ"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a chat with optional LLM parameters"""
    chat_service = ChatService(db)
    message = await chat_service.add_message(chat_id, current_user.id, message_data)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return message


@router.post("/rag", response_model=ChatResponse)
async def rag_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """RAGチャット（モデル指定可能）"""
    try:
        # テナントID取得
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントが設定されていません"
            )
        
        # RAGパイプライン実行
        rag_pipeline = RAGPipeline(db)
        response = await rag_pipeline.generate_response(request, tenant_id)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAGチャットエラー: {str(e)}"
        )


@router.get("/models", response_model=List[str])
async def get_available_models():
    """利用可能なLLMモデル一覧を取得"""
    from app.services.rag_pipeline import LLMService
    llm_service = LLMService()
    return llm_service.get_available_models()
