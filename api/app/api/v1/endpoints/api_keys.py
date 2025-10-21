"""
APIキー管理エンドポイント

このファイルはAPIキー管理に関するAPIエンドポイントを定義します。
APIキーの登録・更新・削除・取得機能を提供します。

主な機能:
- APIキーの登録・更新・削除
- APIキー一覧の取得
- プロバイダー・モデル情報の取得
- テナント管理者専用の機能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.api_key import (
    ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse, ApiKeyListResponse,
    ProviderModelListResponse, ProviderModelInfo
)
from app.services.api_key_service import ApiKeyService
from app.api.v1.deps import get_current_user, require_admin_role
from app.models.user import User
from app.core.exceptions import (
    ApiKeyNotFoundError, ValidationError, BusinessLogicError
)
from app.utils.logging import BusinessLogger, ErrorLogger, logger
from app.core.constants import ApiKeySettings

router = APIRouter()


@router.get("/providers", response_model=ProviderModelListResponse)
async def get_providers_and_models():
    """
    利用可能なプロバイダーとモデル一覧を取得
    
    戻り値:
        ProviderModelListResponse: プロバイダー・モデル一覧
    """
    try:
        providers = []
        for provider in ApiKeySettings.SUPPORTED_PROVIDERS:
            models = ApiKeySettings.get_supported_models(provider)
            providers.append(ProviderModelInfo(
                provider=provider,
                models=models
            ))
        
        return ProviderModelListResponse(providers=providers)
        
    except Exception as e:
        ErrorLogger.error(f"プロバイダー一覧取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プロバイダー一覧の取得に失敗しました"
        )


@router.post("/", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー登録
    
    テナント管理者がLLMプロバイダーのAPIキーを登録します。
    
    引数:
        api_key_data: APIキー作成データ
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyResponse: 作成されたAPIキー情報
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_key = await api_key_service.create_api_key(str(current_user.tenant_id), api_key_data)
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "create_api_key",
            "api_key",
            tenant_id=str(current_user.tenant_id)
        )
        
        return ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            provider=api_key.provider,
            api_key_masked=ApiKeyResponse.mask_api_key(api_key_data.api_key),
            model=api_key.model,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )
        
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        ErrorLogger.error(f"APIキー作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキーの作成に失敗しました"
        )


@router.get("/", response_model=ApiKeyListResponse)
async def get_api_keys(
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー一覧取得
    
    テナントのAPIキー一覧を取得します。
    
    引数:
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyListResponse: APIキー一覧
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_keys = await api_key_service.get_api_keys_by_tenant(str(current_user.tenant_id))
        
        api_key_responses = []
        for api_key in api_keys:
            # マスクされたAPIキーを生成（元のAPIキーは復号化してからマスク）
            decrypted_key = api_key_service.get_decrypted_api_key(api_key)
            masked_key = ApiKeyResponse.mask_api_key(decrypted_key)
            
            api_key_responses.append(ApiKeyResponse(
                id=str(api_key.id),
                tenant_id=str(api_key.tenant_id),
                provider=api_key.provider,
                api_key_masked=masked_key,
                model=api_key.model,
                is_active=api_key.is_active,
                created_at=api_key.created_at,
                updated_at=api_key.updated_at
            ))
        
        return ApiKeyListResponse(
            api_keys=api_key_responses,
            total_count=len(api_key_responses)
        )
        
    except Exception as e:
        ErrorLogger.error(f"APIキー一覧取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキー一覧の取得に失敗しました"
        )


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: str,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー詳細取得
    
    指定されたAPIキーの詳細情報を取得します。
    
    引数:
        api_key_id: APIキーID
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyResponse: APIキー詳細情報
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_key = await api_key_service.get_api_key(api_key_id, str(current_user.tenant_id))
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="APIキーが見つかりません"
            )
        
        # マスクされたAPIキーを生成
        decrypted_key = api_key_service.get_decrypted_api_key(api_key)
        masked_key = ApiKeyResponse.mask_api_key(decrypted_key)
        
        return ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            provider=api_key.provider,
            api_key_masked=masked_key,
            model=api_key.model,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.error(f"APIキー詳細取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキー詳細の取得に失敗しました"
        )


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: str,
    update_data: ApiKeyUpdate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー更新
    
    指定されたAPIキーの情報を更新します。
    
    引数:
        api_key_id: APIキーID
        update_data: 更新データ
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyResponse: 更新されたAPIキー情報
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_key = await api_key_service.update_api_key(
            api_key_id, 
            str(current_user.tenant_id), 
            update_data
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="APIキーが見つかりません"
            )
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "update_api_key",
            "api_key",
            tenant_id=str(current_user.tenant_id)
        )
        
        # マスクされたAPIキーを生成
        decrypted_key = api_key_service.get_decrypted_api_key(api_key)
        masked_key = ApiKeyResponse.mask_api_key(decrypted_key)
        
        return ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            provider=api_key.provider,
            api_key_masked=masked_key,
            model=api_key.model,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )
        
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.error(f"APIキー更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキーの更新に失敗しました"
        )


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー削除
    
    指定されたAPIキーを削除します。
    
    引数:
        api_key_id: APIキーID
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        dict: 削除完了メッセージ
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        success = await api_key_service.delete_api_key(api_key_id, str(current_user.tenant_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="APIキーが見つかりません"
            )
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "delete_api_key",
            "api_key",
            tenant_id=str(current_user.tenant_id)
        )
        
        return {"message": "APIキーが削除されました"}
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.error(f"APIキー削除エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキーの削除に失敗しました"
        )
