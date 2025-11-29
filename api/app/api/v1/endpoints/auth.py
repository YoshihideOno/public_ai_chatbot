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

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.core.database import get_db
from app.schemas.user import UserCreate, Token, UserLogin, PasswordReset, PasswordResetConfirm, EmailVerification, User as UserSchema
from app.models.user import User
from app.schemas.tenant_registration import TenantRegistrationData, TenantRegistrationResponse
from app.services.user_service import UserService
from app.services.tenant_service import TenantService
from app.services.email_service import EmailService
from app.services.token_service import TokenService
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError, InvalidCredentialsError, EmailAlreadyExistsError,
    UsernameAlreadyExistsError, ValidationError, UserNotFoundError
)
from app.utils.logging import BusinessLogger, SecurityLogger, ErrorLogger, logger
from app.utils.common import ValidationUtils

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/register", response_model=None)
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
        # デバッグログ: 受信したデータを確認
        logger.info(f"受信したユーザーデータ: {user_data}")
        logger.info(f"受信したユーザーデータの型: {type(user_data)}")
        logger.info(f"roleの値: {user_data.role}")
        logger.info(f"roleの型: {type(user_data.role)}")
        
        # 入力値のバリデーション
        if not ValidationUtils.validate_email(user_data.email):
            raise ValidationError("無効なメールアドレス形式です")
            
        password_validation = ValidationUtils.validate_password_strength(user_data.password)
        if not password_validation['is_valid']:
            raise ValidationError("パスワードは8文字以上で、大文字、小文字、数字を含む必要があります")
            
        if not ValidationUtils.validate_username(user_data.username):
            raise ValidationError("ユーザー名は3-20文字の英数字とアンダースコアのみ使用可能です")
        
        user_service = UserService(db)
        
        # メールアドレスの重複チェック
        existing_user = await user_service.get_by_email(user_data.email)
        if existing_user:
            SecurityLogger.log_suspicious_activity(
                None,
                "duplicate_email_registration",
                {"email": user_data.email}
            )
            raise EmailAlreadyExistsError()
        
        # ユーザー名の重複チェック
        existing_username = await user_service.get_by_username(user_data.username)
        if existing_username:
            SecurityLogger.log_suspicious_activity(
                None,
                "duplicate_username_registration",
                {"username": user_data.username}
            )
            raise UsernameAlreadyExistsError()
        
        # 新規ユーザー作成
        user = await user_service.create_user(user_data)
        
        # 確認トークンを生成
        plain_token, hashed_token = await TokenService.create_verification_token(
            db, 
            str(user.id), 
            "email_verification", 
            expires_hours=24
        )
        
        # 確認メール送信
        confirmation_url = f"{settings.APP_URL or 'http://localhost:3000'}/verify-email?token={plain_token}"
        email_sent = await EmailService.send_user_registration_email(
            user.email, 
            user.username, 
            confirmation_url
        )
        
        if email_sent:
            logger.info(f"確認メール送信完了: {user.email}")
        else:
            logger.warning(f"確認メール送信失敗: {user.email}")
            
        BusinessLogger.log_user_action(
            str(user.id),
            "register",
            "user",
            tenant_id=str(user.tenant_id) if user.tenant_id else None
        )
        return user
        
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError, ValidationError):
        raise
    except Exception as e:
        ErrorLogger.log_exception(e, {"operation": "user_registration"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー登録に失敗しました"
        )


@router.post("/verify-email")
async def verify_email(
    token: str = Query(..., description="確認トークン"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    メール確認処理
    
    確認トークンを使用してユーザーのメールアドレスを確認します。
    トークンが有効な場合、ユーザーのis_verifiedフラグをtrueに設定します。
    
    引数:
        token: 確認トークン（クエリパラメータ）
        request: FastAPIのRequestオブジェクト
        db: データベースセッション
        
    戻り値:
        dict: 確認結果
        
    例外:
        HTTPException: トークンが無効または期限切れ
    """
    try:
        # トークンを検証
        user = await TokenService.verify_token(db, token, "email_verification")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なトークンまたは期限切れです"
            )
        
        # ユーザーのメール確認状態を更新
        user.is_verified = True
        await db.commit()
        
        # メール確認を監査ログに記録
        BusinessLogger.log_user_action(
            str(user.id),
            "verify_email",
            "auth",
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            request=request
        )
        
        logger.info(f"メール確認完了: {user.email}")
        
        return {
            "message": "メールアドレスの確認が完了しました",
            "user_id": str(user.id),
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.log_exception(e, {"operation": "verify_email", "token": token})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メール確認処理に失敗しました"
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token"""
    user_service = UserService(db)
    
    # Authenticate user
    user = await user_service.authenticate(login_data.email, login_data.password)
    if not user:
        # ログイン失敗を監査ログに記録
        tenant_id = None
        try:
            # ユーザーが見つからない場合でも、メールアドレスからテナントを推測できないためスキップ
            pass
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # 非アクティブユーザーのログイン試行を監査ログに記録
        BusinessLogger.log_user_action(
            str(user.id),
            "login_failed_inactive",
            "auth",
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            request=request
        )
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
    
    # ログイン成功を監査ログに記録
    BusinessLogger.log_user_action(
        str(user.id),
        "login_success",
        "auth",
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        request=request
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/login/oauth", response_model=Token)
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
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
        # 非アクティブユーザーのログイン試行を監査ログに記録
        BusinessLogger.log_user_action(
            str(user.id),
            "login_failed_inactive",
            "auth",
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            request=request
        )
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
    
    # ログイン成功を監査ログに記録
    BusinessLogger.log_user_action(
        str(user.id),
        "login_success_oauth",
        "auth",
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        request=request
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    request: Request = None,
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
        user = await user_service.get_by_id(user_id)
        
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
        
        # トークンリフレッシュを監査ログに記録
        BusinessLogger.log_user_action(
            str(user.id),
            "token_refresh",
            "auth",
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            request=request
        )
        
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
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should discard tokens)"""
    # In a stateless JWT system, logout is handled client-side
    # by discarding the tokens. Server-side logout would require
    # maintaining a blacklist of tokens, which is not implemented here.
    
    # ログアウトを監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "logout",
        "auth",
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        request=request
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=None)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    request: Request,
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
    
    # パスワードリセット要求を監査ログに記録
    BusinessLogger.log_user_action(
        str(user.id),
        "password_reset_request",
        "auth",
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        request=request
    )
    
    # TODO: Send email with reset token
    # For now, just return success message
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
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
        user = await user_service.get_by_id(user_id)
        success = await user_service.update_password(user_id, reset_data.new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
        
        # パスワードリセット実行を監査ログに記録
        if user:
            BusinessLogger.log_user_action(
                str(user.id),
                "password_reset_confirm",
                "auth",
                tenant_id=str(user.tenant_id) if user.tenant_id else None,
                request=request
            )
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )


@router.post("/register-tenant", response_model=TenantRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    registration_data: TenantRegistrationData,
    db: AsyncSession = Depends(get_db)
):
    """
    テナント登録
    
    テナント作成とテナント管理者ユーザー作成を同時に行います。
    同一トランザクション内でテナントとユーザーを作成し、メール認証を実行します。
    
    引数:
        registration_data: テナント登録データ
        db: データベースセッション
        
    戻り値:
        TenantRegistrationResponse: 登録完了レスポンス
        
    例外:
        EmailAlreadyExistsError: メールアドレス重複
        UsernameAlreadyExistsError: ユーザー名重複
        ValidationError: バリデーションエラー
    """
    try:
        logger.info(f"テナント登録開始: {registration_data.tenant_name}, {registration_data.admin_email}")
        
        # サービス初期化
        tenant_service = TenantService(db)
        user_service = UserService(db)
        
        logger.info("重複チェック開始")
        # メールアドレスとユーザー名の重複チェック（単一クエリで実行）
        from sqlalchemy import or_
        existing_user_query = await db.execute(
            select(User).where(
                or_(
                    User.email == registration_data.admin_email,
                    User.username == registration_data.admin_username
                )
            )
        )
        existing_user = existing_user_query.scalar_one_or_none()
        
        if existing_user:
            if existing_user.email == registration_data.admin_email:
                SecurityLogger.log_suspicious_activity(
                    None,
                    "duplicate_email_tenant_registration",
                    {"email": registration_data.admin_email}
                )
                raise EmailAlreadyExistsError()
            else:
                SecurityLogger.log_suspicious_activity(
                    None,
                    "duplicate_username_tenant_registration",
                    {"username": registration_data.admin_username}
                )
                raise UsernameAlreadyExistsError()
        
        logger.info("ユーザー重複チェック完了")
        
        # テナントドメインの重複チェック
        existing_tenant = await tenant_service.get_by_domain(registration_data.tenant_domain)
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このドメインは既に使用されています"
            )
        
        logger.info("テナントドメイン重複チェック完了")
        
        # トランザクション開始
        logger.info("トランザクション開始")
        # テナント作成
        from app.schemas.tenant import TenantCreate
        from app.core.constants import PlanLimits
        
        logger.info("テナント作成開始")
        tenant_create_data = TenantCreate(
            name=registration_data.tenant_name,
            domain=registration_data.tenant_domain,
            plan="FREE",
            status="ACTIVE",
            settings={
                "max_storage_mb": PlanLimits.BASIC_PLAN_MAX_STORAGE_MB,
                "max_queries_per_day": PlanLimits.BASIC_PLAN_MAX_QUERIES_PER_DAY,
                "default_model": "gpt-4",
                "chunk_size": 1024,
                "chunk_overlap": 200,
                "enable_api_access": True,
                "enable_webhook": False,
            }
        )
        
        tenant = await tenant_service.create_tenant(tenant_create_data)
        logger.info(f"テナント作成完了: {tenant.id}")
        
        # テナント管理者ユーザー作成
        from app.models.user import UserRole
        from app.schemas.user import UserCreate
        
        logger.info("テナント管理者ユーザー作成開始")
        admin_user_data = UserCreate(
            email=registration_data.admin_email,
            username=registration_data.admin_username,
            password=registration_data.admin_password,
            role=UserRole.TENANT_ADMIN,
            tenant_id=str(tenant.id)
        )
        
        admin_user = await user_service.create_user(admin_user_data)
        logger.info(f"テナント管理者ユーザー作成完了: {admin_user.id}")
        
        # ビジネスログ記録
        BusinessLogger.log_user_action(
            str(admin_user.id),
            "register_tenant",
            "tenant",
            tenant_id=str(tenant.id)
        )
        
        logger.info("トランザクション内処理完了")
        
        # レスポンス用のデータを保存
        response_data = TenantRegistrationResponse(
            tenant_id=str(tenant.id),
            tenant_name=tenant.name,
            admin_user_id=str(admin_user.id),
            admin_email=admin_user.email,
            message="テナント登録が完了しました。確認メールをご確認ください。"
        )
        
        # メール送信用のデータを保存
        email_data = {
            "user_id": str(admin_user.id),
            "email": admin_user.email,
            "username": admin_user.username
        }
        
        logger.info("トランザクション完了")
        
        # トランザクション外でメール送信（非同期処理）
        logger.info("メール送信処理開始")
        try:
            # 確認トークンを生成（トランザクション外）
            plain_token, hashed_token = await TokenService.create_verification_token(
                db, 
                email_data["user_id"], 
                "email_verification", 
                expires_hours=24
            )
            logger.info("確認トークン生成完了")
            
            # 確認メール送信
            confirmation_url = f"{settings.APP_URL or 'http://localhost:3000'}/verify-email?token={plain_token}"
            email_sent = await EmailService.send_user_registration_email(
                email_data["email"], 
                email_data["username"], 
                confirmation_url
            )
            
            if email_sent:
                logger.info(f"テナント管理者確認メール送信完了: {email_data['email']}")
            else:
                logger.warning(f"テナント管理者確認メール送信失敗: {email_data['email']}")
                
        except Exception as e:
            logger.error(f"メール送信エラー: {str(e)}")
            # メール送信失敗は登録を阻害しない
        
        logger.info("テナント登録処理完了")
        return response_data
        
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError, ValidationError):
        raise
    except Exception as e:
        ErrorLogger.log_exception(
            "tenant_registration_error",
            str(e),
            {"tenant_name": registration_data.tenant_name, "admin_email": registration_data.admin_email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="テナント登録に失敗しました"
        )
