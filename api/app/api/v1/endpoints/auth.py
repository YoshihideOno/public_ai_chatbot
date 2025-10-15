"""
認証エンドポイント

このファイルはユーザー認証に関するAPIエンドポイントを定義します。
ログイン、ログアウト、ユーザー登録、パスワードリセットなどの認証機能を提供します。

主な機能:
- ユーザー登録
- ログイン・ログアウト
- トークン管理（アクセス・リフレッシュ）
- パスワードリセット
- ユーザー認証状態確認
- OAuth2認証
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.core.database import get_db
from app.schemas.user import User, UserCreate, Token, UserLogin, PasswordReset, PasswordResetConfirm
from app.services.user_service import UserService
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError, InvalidCredentialsError, EmailAlreadyExistsError,
    UsernameAlreadyExistsError, ValidationError, UserNotFoundError
)
from app.utils.logging import BusinessLogger, SecurityLogger
from app.utils.common import ValidationUtils

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    新規ユーザー登録
    
    新しいユーザーアカウントを作成します。
    メールアドレスとユーザー名の重複チェック、パスワードのハッシュ化を行います。
    
    引数:
        user_data: ユーザー作成データ
        db: データベースセッション
        
    戻り値:
        User: 作成されたユーザー情報
        
    例外:
        EmailAlreadyExistsError: メールアドレス重複
        UsernameAlreadyExistsError: ユーザー名重複
        ValidationError: バリデーションエラー
    """
    try:
        # 入力値のバリデーション
        if not ValidationUtils.is_valid_email(user_data.email):
            raise ValidationError("無効なメールアドレス形式です")
            
        if not ValidationUtils.is_valid_password(user_data.password):
            raise ValidationError("パスワードは8文字以上で、英数字と記号を含む必要があります")
            
        if not ValidationUtils.is_valid_username(user_data.username):
            raise ValidationError("ユーザー名は3-20文字の英数字とアンダースコアのみ使用可能です")
        
        user_service = UserService(db)
        
        # メールアドレスの重複チェック
        existing_user = await user_service.get_by_email(user_data.email)
        if existing_user:
            SecurityLogger.warning(f"メールアドレス重複試行: {user_data.email}")
            raise EmailAlreadyExistsError()
        
        # ユーザー名の重複チェック
        existing_username = await user_service.get_by_username(user_data.username)
        if existing_username:
            SecurityLogger.warning(f"ユーザー名重複試行: {user_data.username}")
            raise UsernameAlreadyExistsError()
        
        # 新規ユーザー作成
        user = await user_service.create_user(user_data)
        BusinessLogger.info(f"新規ユーザー登録完了: {user.email}")
        return user
        
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError, ValidationError):
        raise
    except Exception as e:
        BusinessLogger.error(f"ユーザー登録エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー登録に失敗しました"
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token"""
    user_service = UserService(db)
    
    # Authenticate user
    user = await user_service.authenticate(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await user_service.update_last_login(user.id)
    
    # Create tokens
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/login/oauth", response_model=Token)
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login user with OAuth2 password flow"""
    user_service = UserService(db)
    
    # Authenticate user
    user = await user_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await user_service.update_last_login(user.id)
    
    # Create tokens
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_token(refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user_service = UserService(db)
        user = await user_service.get_by_id(int(user_id))
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should discard tokens)"""
    # In a stateless JWT system, logout is handled client-side
    # by discarding the tokens. Server-side logout would require
    # maintaining a blacklist of tokens, which is not implemented here.
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    user_service = UserService(db)
    
    user = await user_service.get_by_email(reset_data.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = create_access_token(
        {"sub": str(user.id), "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )
    
    # TODO: Send email with reset token
    # For now, just return success message
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset"""
    try:
        # Verify reset token
        payload = verify_token(reset_data.token)
        
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Update password
        user_service = UserService(db)
        success = await user_service.update_password(int(user_id), reset_data.new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
