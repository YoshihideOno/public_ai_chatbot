"""
依存性注入モジュール

このファイルはFastAPIの依存性注入システムで使用される関数を定義します。
認証、認可、データベースセッションなどの共通的な依存関係を管理します。

主な機能:
- 現在のユーザー取得
- ロールベース認可
- テナントアクセス制御
- データベースセッション管理
- 認証トークン検証
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.core.security import verify_token, extract_user_id_from_token
from app.services.user_service import UserService
from app.schemas.user import User
from app.models.user import UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError, UserNotFoundError
from app.utils.logging import SecurityLogger

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_service = UserService(db)
    # user_idはUUID文字列のため、そのまま渡す
    user = await user_service.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_roles(required_roles: List[UserRole]):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


def require_admin_role():
    """Require admin role (PLATFORM_ADMIN or TENANT_ADMIN)"""
    return require_roles([UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN])


def require_platform_admin():
    """Require platform admin role"""
    return require_roles([UserRole.PLATFORM_ADMIN])


def require_tenant_admin():
    """Require tenant admin role"""
    return require_roles([UserRole.TENANT_ADMIN])


def require_operator_or_above():
    """Require operator role or above"""
    return require_roles([UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN, UserRole.OPERATOR])


def require_auditor_or_above():
    """Require auditor role or above"""
    return require_roles([UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN, UserRole.AUDITOR])


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
        
        user_service = UserService(db)
        user = await user_service.get_by_id(user_id)
        
        if user and user.is_active:
            return user
    except HTTPException:
        pass
    
    return None


async def get_tenant_from_user(
    current_user: User = Depends(get_current_active_user)
) -> Optional[str]:
    """Get tenant ID from current user"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        return None  # Platform admin can access all tenants
    return current_user.tenant_id