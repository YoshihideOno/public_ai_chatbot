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

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.core.security import verify_token, extract_user_id_from_token
from app.services.user_service import UserService
from app.services.tenant_service import TenantService
from app.schemas.user import User
from app.models.user import UserRole
from app.models.tenant import Tenant
from app.core.exceptions import AuthenticationError, AuthorizationError, UserNotFoundError
from app.utils.logging import SecurityLogger, logger

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
        # ロールを比較（Enum値と文字列の両方に対応）
        user_role = current_user.role
        if isinstance(user_role, str):
            user_role = UserRole(user_role)
        
        if user_role not in required_roles:
            from app.utils.logging import logger
            logger.warning(f"権限不足: ユーザーロール={user_role}, 必要なロール={required_roles}")
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


def require_admin_or_auditor():
    """Require admin role (PLATFORM_ADMIN or TENANT_ADMIN) or AUDITOR for read-only access"""
    return require_roles([UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN, UserRole.AUDITOR])


def require_tenant_user():
    """Require any tenant user (PLATFORM_ADMIN, TENANT_ADMIN, OPERATOR, or AUDITOR)"""
    return require_roles([UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN, UserRole.OPERATOR, UserRole.AUDITOR])


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


async def get_tenant_from_widget_auth(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="テナントID"),
    x_api_key: str = Header(..., alias="X-API-Key", description="テナントAPIキー"),
    origin: Optional[str] = Header(None, alias="Origin", description="リクエスト元オリジン"),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """
    Widget用認証: テナントID・APIキー・オリジンで認証
    
    引数:
        x_tenant_id: リクエストヘッダーから取得するテナントID
        x_api_key: リクエストヘッダーから取得するAPIキー
        origin: ブラウザから送信されるOriginヘッダー（ウィジェット設置オリジン）
        db: データベースセッション
        
    戻り値:
        Tenant: 認証されたテナントオブジェクト
        
    例外:
        HTTPException: 認証に失敗した場合
    """
    try:
        # テナントサービスを使用してAPIキーでテナントを取得
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_by_api_key(x_api_key)
        
        if not tenant:
            SecurityLogger.warning(f"無効なAPIキー: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Widget"},
            )
        
        # テナントIDの検証
        if str(tenant.id) != x_tenant_id:
            SecurityLogger.warning(
                f"テナントID不一致: リクエスト={x_tenant_id}, DB={tenant.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant ID mismatch",
                headers={"WWW-Authenticate": "Widget"},
            )
        
        # テナントのステータス確認
        if tenant.status != "ACTIVE":
            SecurityLogger.warning(
                f"非アクティブテナント: tenant_id={tenant.id}, status={tenant.status}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant is not active",
            )

        # ウィジェット許可オリジンの検証（allowed_widget_originsはCSV形式）
        try:
            raw_origins = (tenant.allowed_widget_origins or "").strip()
            allowed_origins: List[str] = []
            if raw_origins:
                allowed_origins = [
                    o.strip()
                    for o in raw_origins.split(",")
                    if o.strip()
                ]
        except Exception as parse_error:
            logger.error(
                "ウィジェット許可オリジンの解析に失敗しました",
                error=str(parse_error),
            )
            allowed_origins = []

        # Originヘッダが存在し、許可オリジンが設定されている場合のみチェックを行う
        if origin and allowed_origins:
            if origin not in allowed_origins:
                SecurityLogger.warning(
                    f"許可されていないオリジンからのウィジェットアクセス: "
                    f"tenant_id={tenant.id}, origin={origin}, allowed_origins={allowed_origins}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Origin not allowed",
                )
        # Originが存在しない場合や許可オリジンが未設定の場合は、
        # 既存環境との互換性のためここでは拒否せず通過させる。
        # 実運用ではallowed_widget_originsを設定することを推奨。
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Widget認証エラー",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )