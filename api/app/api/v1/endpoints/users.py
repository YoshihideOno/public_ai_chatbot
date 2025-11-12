from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import Response
from io import StringIO
import csv
from datetime import datetime as dt
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserCreate
from app.services.user_service import UserService
from app.api.v1.deps import (
    get_current_user, 
    get_current_active_user, 
    require_admin_role, 
    require_platform_admin,
    require_tenant_admin,
    require_admin_or_auditor,
    get_tenant_from_user
)
from app.models.user import UserRole
from app.core.exceptions import ValidationError
from app.utils.logging import BusinessLogger

router = APIRouter()


@router.get("/me", response_model=None)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=None)
async def update_current_user(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    user_service = UserService(db)
    
    # Users cannot change their own role
    if user_update.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    updated_user = await user_service.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 自己更新を監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "update_current_user",
        "user",
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        request=request,
        resource_id=str(current_user.id)
    )
    
    return updated_user


@router.delete("/me")
async def delete_current_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user account (soft delete)"""
    user_service = UserService(db)
    success = await user_service.delete_user(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 自己削除を監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "delete_current_user",
        "user",
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        request=request,
        resource_id=str(current_user.id)
    )
    
    return {"message": "User account deleted successfully"}


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin_or_auditor()),
    db: AsyncSession = Depends(get_db)
):
    """Get users list (admin only)"""
    user_service = UserService(db)
    
    # Platform admin can see all users
    if current_user.role == UserRole.PLATFORM_ADMIN:
        users = await user_service.get_all_users(skip=skip, limit=limit)
    else:
        # Tenant admin can only see users in their tenant
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenant access"
            )
        users = await user_service.get_users_by_tenant(tenant_id, skip=skip, limit=limit)
    
    return users


@router.post("/", response_model=None)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    user_service = UserService(db)
    
    # Check if active user already exists（非アクティブは許容: サービス側で再有効化される）
    existing_user = await user_service.get_by_email(user_data.email)
    if existing_user and existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_username = await user_service.get_by_username(user_data.username)
    if existing_username and existing_username.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Tenant admin can only create users in their tenant
    tenant_id = None
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenant access"
            )
        user_data.tenant_id = tenant_id
        
        # Tenant admin cannot create platform admin users
        if user_data.role == UserRole.PLATFORM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create platform admin users"
            )
    else:
        tenant_id = str(user_data.tenant_id) if user_data.tenant_id else None
    
    user = await user_service.create_user(user_data)
    
    # ユーザー作成を監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "create_user",
        "user",
        tenant_id=tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None),
        request=request,
        resource_id=str(user.id)
    )
    
    return user


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin_or_auditor()),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)"""
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user_service = UserService(db)
    user = await user_service.get_by_id(user_uuid)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Tenant admin can only access users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return user


@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """Update user by ID (admin only)"""
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_uuid)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Tenant admin restrictions
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        # Tenant admin may change roles only between OPERATOR and AUDITOR
        if user_update.role is not None:
            if user_update.role == UserRole.PLATFORM_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot change user role to platform admin"
                )
            # 変更対象が管理者の場合は不可
            if target_user.role in [UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot change admin user's role"
                )
            # 許可ロールは OPERATOR / AUDITOR のみ
            if user_update.role not in [UserRole.OPERATOR, UserRole.AUDITOR]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant admin can only set role to OPERATOR or AUDITOR"
                )
    
    updated_user = await user_service.update_user(user_uuid, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # ユーザー更新を監査ログに記録
    tenant_id = str(target_user.tenant_id) if target_user.tenant_id else None
    BusinessLogger.log_user_action(
        str(current_user.id),
        "update_user",
        "user",
        tenant_id=tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None),
        request=request,
        resource_id=user_id
    )
    
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """Delete user by ID (admin only)"""
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_uuid)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # 管理者ロールのユーザーは削除不可
    if target_user.role == UserRole.PLATFORM_ADMIN or target_user.role == UserRole.TENANT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者ロールのユーザーは削除できません"
        )
    
    # Tenant admin can only delete users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await user_service.delete_user(user_uuid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # ユーザー削除を監査ログに記録
    tenant_id = str(target_user.tenant_id) if target_user.tenant_id else None
    BusinessLogger.log_user_action(
        str(current_user.id),
        "delete_user",
        "user",
        tenant_id=tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None),
        request=request,
        resource_id=user_id
    )
    
    return {"message": "User deleted successfully"}


@router.get("/actions/export")
async def export_users(
    format: str = Query("csv"),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    request: Request = None,
    current_user: User = Depends(require_admin_or_auditor()),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザー一覧のエクスポート（CSV/JSON）

    引数:
      format: 出力形式（csv|json）
      search: ユーザー名/メールの部分一致フィルタ
      role: ロールでのフィルタ
      is_active: アクティブ状態でのフィルタ

    戻り値:
      Response: ダウンロードレスポンス
    """
    user_service = UserService(db)

    # テナント境界：プラットフォーム管理者は全件、テナント管理者・監査者は自テナントのみ
    if current_user.role == UserRole.PLATFORM_ADMIN:
        fetch_all = True
        tenant_id = None
    else:
        fetch_all = False
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenant access")

    # 役割フィルタを正規化
    role_enum = None
    if role:
        try:
            role_enum = UserRole(role)
        except ValueError:
            raise ValidationError(f"無効なロール: {role}")

    # データ取得（最大1000件まで）
    if fetch_all:
        users = await user_service.get_all_users(skip=0, limit=1000)
    else:
        users = await user_service.get_users_by_tenant(tenant_id, skip=0, limit=1000)

    # フィルタ適用（簡易）
    def matches(u) -> bool:
        if role_enum and getattr(u, 'role', None) != role_enum:
            return False
        if is_active is not None and getattr(u, 'is_active', None) is not is_active:
            return False
        if search:
            s = search.lower()
            name_ok = (u.username or '').lower().find(s) >= 0
            mail_ok = (u.email or '').lower().find(s) >= 0
            if not (name_ok or mail_ok):
                return False
        return True

    filtered = [u for u in users if matches(u)]

    # 出力行
    rows = []
    for u in filtered:
        rows.append({
            "id": str(u.id) if u.id else None,
            "email": u.email,
            "username": u.username,
            "role": u.role.value if getattr(u, 'role', None) else None,
            "tenant_id": str(u.tenant_id) if getattr(u, 'tenant_id', None) else None,
            "is_active": bool(getattr(u, 'is_active', False)),
            "created_at": u.created_at.isoformat() if getattr(u, 'created_at', None) else None,
            "updated_at": u.updated_at.isoformat() if getattr(u, 'updated_at', None) else None,
            "last_login_at": u.last_login_at.isoformat() if getattr(u, 'last_login_at', None) else None,
        })

    # 監査ログ
    BusinessLogger.log_user_action(
        str(current_user.id),
        "export_users",
        "users_export",
        tenant_id=None if fetch_all else str(tenant_id),
        request=request
    )

    ts = dt.utcnow().strftime('%Y%m%d_%H%M%S')
    if format.lower() == 'json':
        import json
        payload = json.dumps(rows, ensure_ascii=False)
        headers = {"Content-Disposition": f"attachment; filename=users_{ts}.json"}
        return Response(content=payload.encode('utf-8'), media_type='application/json; charset=utf-8', headers=headers)

    if format.lower() != 'csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="formatはcsvまたはjsonのみ対応しています")

    output = StringIO()
    fieldnames = ["id", "email", "username", "role", "tenant_id", "is_active", "created_at", "updated_at", "last_login_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    csv_bytes = output.getvalue().encode('utf-8')
    headers = {"Content-Disposition": f"attachment; filename=users_{ts}.csv"}
    return Response(content=csv_bytes, media_type='text/csv; charset=utf-8', headers=headers)


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """Activate user account (admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Tenant admin can only activate users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await user_service.activate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # ユーザーアクティベートを監査ログに記録
    tenant_id = str(target_user.tenant_id) if target_user.tenant_id else None
    BusinessLogger.log_user_action(
        str(current_user.id),
        "activate_user",
        "user",
        tenant_id=tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None),
        request=request,
        resource_id=str(user_id)
    )
    
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account (admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot deactivate yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Tenant admin can only deactivate users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # ユーザー非アクティベートを監査ログに記録
    tenant_id = str(target_user.tenant_id) if target_user.tenant_id else None
    BusinessLogger.log_user_action(
        str(current_user.id),
        "deactivate_user",
        "user",
        tenant_id=tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None),
        request=request,
        resource_id=str(user_id)
    )
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/change-role")
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    request: Request,
    current_user: User = Depends(require_platform_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Change user role (platform admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await user_service.change_user_role(user_id, new_role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # ロール変更を監査ログに記録
    tenant_id = str(target_user.tenant_id) if target_user.tenant_id else None
    BusinessLogger.log_user_action(
        str(current_user.id),
        "change_user_role",
        "user",
        tenant_id=tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None),
        request=request,
        resource_id=str(user_id),
        old_role=target_user.role.value if target_user.role else None,
        new_role=new_role.value
    )
    
    return {"message": f"User role changed to {new_role.value}"}
