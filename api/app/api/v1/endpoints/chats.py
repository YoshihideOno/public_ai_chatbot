from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_pipeline import RAGPipeline
from app.api.v1.deps import get_current_user, get_tenant_from_widget_auth
from app.schemas.user import User
from app.models.tenant import Tenant

router = APIRouter()


@router.post("/rag", response_model=ChatResponse)
async def rag_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """RAGチャット（モデル指定可能）"""
    try:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントが設定されていません"
            )

        rag_pipeline = RAGPipeline(db)
        response = await rag_pipeline.generate_response(request, tenant_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAGチャットエラー: {str(e)}"
        )


@router.post("/widget/chat", response_model=ChatResponse)
async def widget_rag_chat(
    request: ChatRequest,
    tenant: Tenant = Depends(get_tenant_from_widget_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Widget用RAGチャット（認証不要、テナントID+APIキーで認証）

    会話ログはconversationsテーブルとusage_logsテーブルに自動保存されます。
    """
    try:
        tenant_id = str(tenant.id)
        rag_pipeline = RAGPipeline(db)
        response = await rag_pipeline.generate_response(request, tenant_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        from app.utils.logging import ErrorLogger
        ErrorLogger.log_exception(e, {"tenant_id": str(tenant.id), "query": request.query})
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
