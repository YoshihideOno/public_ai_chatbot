from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.schemas.tenant import (
    Tenant, TenantPublic, TenantCreate, TenantUpdate, TenantStats, 
    TenantSettings, TenantEmbedSnippet
)
from app.schemas.user import User
from app.services.tenant_service import TenantService
from app.api.v1.deps import (
    get_current_user, 
    require_platform_admin,
    require_admin_role,
    require_operator_or_above,
    require_admin_or_auditor,
    require_tenant_user,
    get_tenant_from_user
)
from app.models.user import UserRole
from app.core.exceptions import (
    TenantNotFoundError, ConflictError, 
    TenantAccessDeniedError, ValidationError
)
from app.utils.logging import BusinessLogger, SecurityLogger
from app.utils.common import PaginationUtils

router = APIRouter()


@router.get("/", response_model=List[TenantPublic])
async def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_platform_admin()),
    db: AsyncSession = Depends(get_db)
):
    """テナント一覧取得（Platform Admin専用）"""
    tenant_service = TenantService(db)
    tenants = await tenant_service.get_all_tenants(
        skip=skip, 
        limit=limit, 
        status=status
    )
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "list_tenants",
        "tenants",
        tenant_id=None
    )
    
    return tenants


@router.get("/{tenant_id}/embed-snippet", response_model=TenantEmbedSnippet)
async def get_embed_snippet(
    tenant_id: str,
    current_user: User = Depends(require_tenant_user()),
    db: AsyncSession = Depends(get_db)
):
    """埋め込みスニペット取得（テナント所属全ユーザーがアクセス可能）"""
    from app.utils.logging import logger
    
    try:
        logger.info(f"埋め込みスニペット取得リクエスト: tenant_id={tenant_id}, user_id={current_user.id}, role={current_user.role}")
        
        tenant_service = TenantService(db)
        
        # アクセス権限チェック
        if current_user.role != UserRole.PLATFORM_ADMIN:
            if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
                logger.warning(f"テナントアクセス拒否: tenant_id={tenant_id}, user_id={current_user.id}")
                raise TenantAccessDeniedError()
        
        snippet = await tenant_service.generate_embed_snippet(tenant_id)
        if not snippet:
            logger.error(f"埋め込みスニペット生成失敗: tenant_id={tenant_id}")
            raise TenantNotFoundError()
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "get_embed_snippet",
            "embed_snippet",
            tenant_id=tenant_id
        )
        
        logger.info(f"埋め込みスニペット取得成功: tenant_id={tenant_id}")
        return snippet
        
    except Exception as e:
        logger.error(f"埋め込みスニペット取得エラー: tenant_id={tenant_id}, error={str(e)}", exc_info=True)
        raise


@router.get("/{tenant_id}", response_model=TenantPublic)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(require_tenant_user()),
    db: AsyncSession = Depends(get_db)
):
    """テナント詳細取得（テナント所属全ユーザーがアクセス可能）"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        # 自テナントであれば許可
        if str(current_user.tenant_id) != tenant_id:
            if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
                raise TenantAccessDeniedError()
    
    tenant = await tenant_service.get_by_id(tenant_id)
    if not tenant:
        raise TenantNotFoundError()
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "get_tenant",
        "tenant",
        tenant_id=tenant_id
    )
    
    return tenant


@router.put("/{tenant_id}", response_model=TenantPublic)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """テナント更新"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if str(current_user.tenant_id) != tenant_id:
            if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
                raise TenantAccessDeniedError()
    
    try:
        tenant = await tenant_service.update_tenant(tenant_id, tenant_update)
        if not tenant:
            raise TenantNotFoundError()
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "update_tenant",
            "tenant",
            tenant_id=tenant_id,
            request=request,
            resource_id=tenant_id
        )
        
        return tenant
        
    except ValueError as e:
        raise ConflictError(str(e))


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    request: Request,
    current_user: User = Depends(require_platform_admin()),
    db: AsyncSession = Depends(get_db)
):
    """テナント削除（Platform Admin専用）"""
    tenant_service = TenantService(db)
    
    success = await tenant_service.delete_tenant(tenant_id)
    if not success:
        raise TenantNotFoundError()
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "delete_tenant",
        "tenant",
        tenant_id=tenant_id,
        request=request,
        resource_id=tenant_id
    )
    
    return {"message": "テナントが削除されました"}


@router.get("/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: str,
    current_user: User = Depends(require_admin_or_auditor()),
    db: AsyncSession = Depends(get_db)
):
    """テナント統計取得"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if str(current_user.tenant_id) != tenant_id:
            if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
                raise TenantAccessDeniedError()
    
    stats = await tenant_service.get_tenant_stats(tenant_id)
    if not stats:
        raise TenantNotFoundError()
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "get_tenant_stats",
        "tenant_stats",
        tenant_id=tenant_id
    )
    
    return stats


@router.put("/{tenant_id}/settings")
async def update_tenant_settings(
    tenant_id: str,
    settings: Dict[str, Any],
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    テナント設定更新
    
    部分更新をサポートします。null値のフィールドは削除されます。
    """
    # ログ出力（BusinessLoggerを使用）
    BusinessLogger.log_tenant_action(
        tenant_id,
        "settings_update_request",
        {"request_settings": settings}
    )
    
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if str(current_user.tenant_id) != tenant_id:
            if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
                raise TenantAccessDeniedError()
    
    # バリデーション: 送信されたフィールドのみを検証
    # TenantSettingsのフィールド名リストを取得（Pydantic v1とv2で異なる）
    try:
        # Pydantic v2の場合
        valid_fields = set(TenantSettings.model_fields.keys())
    except AttributeError:
        # Pydantic v1の場合
        valid_fields = set(TenantSettings.__fields__.keys())
    
    validated_settings = {}
    
    for key, value in settings.items():
        if key in valid_fields:
            # None値もそのまま渡す（後で削除される）
            validated_settings[key] = value
    
    # バリデーション後のログ
    BusinessLogger.log_tenant_action(
        tenant_id,
        "settings_validated",
        {"validated_settings": validated_settings}
    )
    
    # バリデーション: Noneでない値のみ検証
    try:
        for key, value in validated_settings.items():
            if value is not None:
                # Noneでない場合のみバリデーション
                if key == 'default_model' or key == 'embedding_model':
                    available_models = [
                        "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini",
                        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3-5-sonnet",
                        "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"
                    ]
                    if value not in available_models:
                        raise ValidationError(f'サポートされていないモデル: {value}')
    except ValueError as e:
        raise ValidationError(str(e))
    
    # サービス層で更新（Dictとして直接渡す）
    success = await tenant_service.update_tenant_settings_dict(tenant_id, validated_settings)
    if not success:
        raise TenantNotFoundError()
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "update_tenant_settings",
        "tenant_settings",
        tenant_id=tenant_id,
        request=request,
        resource_id=tenant_id
    )
    
    return {"message": "設定が更新されました"}


@router.post("/{tenant_id}/regenerate-api-key")
async def regenerate_api_key(
    tenant_id: str,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """APIキー再発行"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
            raise TenantAccessDeniedError()
    
    new_api_key = await tenant_service.regenerate_api_key(tenant_id)
    if not new_api_key:
        raise TenantNotFoundError()
    
    SecurityLogger.log_suspicious_activity(
        str(current_user.id),
        "api_key_regenerated",
        {"tenant_id": tenant_id},
        tenant_id=tenant_id,
        request=request
    )
    
    return {"api_key": new_api_key}


@router.get("/{tenant_id}/users")
async def get_tenant_users(
    tenant_id: str,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """テナントのユーザー一覧取得"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
            raise TenantAccessDeniedError()
    
    users = await tenant_service.get_tenant_users(tenant_id)
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "get_tenant_users",
        "tenant_users",
        tenant_id=tenant_id
    )
    
    return users


@router.post("/{tenant_id}/users/{user_id}")
async def add_user_to_tenant(
    tenant_id: str,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """テナントにユーザー追加"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
            raise TenantAccessDeniedError()
    
    success = await tenant_service.add_user_to_tenant(tenant_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーの追加に失敗しました"
        )
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "add_user_to_tenant",
        "tenant_user",
        tenant_id=tenant_id,
        request=request,
        resource_id=str(user_id)
    )
    
    return {"message": "ユーザーがテナントに追加されました"}


@router.delete("/{tenant_id}/users/{user_id}")
async def remove_user_from_tenant(
    tenant_id: str,
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """テナントからユーザー削除"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
            raise TenantAccessDeniedError()
    
    success = await tenant_service.remove_user_from_tenant(tenant_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーの削除に失敗しました"
        )
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "remove_user_from_tenant",
        "tenant_user",
        tenant_id=tenant_id,
        request=request,
        resource_id=str(user_id)
    )
    
    return {"message": "ユーザーがテナントから削除されました"}


@router.get("/{tenant_id}/usage-summary")
async def get_tenant_usage_summary(
    tenant_id: str,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """テナント使用量サマリ取得"""
    tenant_service = TenantService(db)
    
    # アクセス権限チェック
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if not await tenant_service.validate_tenant_access(tenant_id, current_user.id):
            raise TenantAccessDeniedError()
    
    usage_summary = await tenant_service.get_tenant_usage_summary(tenant_id)
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "get_tenant_usage_summary",
        "tenant_usage",
        tenant_id=tenant_id
    )
    
    return usage_summary
