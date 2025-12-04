"""
ユーザー管理サービス

このファイルはユーザーに関するビジネスロジックを実装します。
ユーザーのCRUD操作、認証、権限管理、テナント関連付けなどの機能を提供します。

主な機能:
- ユーザーの作成・更新・削除
- ユーザー検索（ID、メール、ユーザー名）
- パスワード管理（ハッシュ化・検証）
- ロール管理（RBAC）
- テナント関連付け
- ユーザー状態管理（アクティブ・非アクティブ）
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import (
    UserNotFoundError, EmailAlreadyExistsError, UsernameAlreadyExistsError,
    ValidationError, BusinessLogicError
)
from app.utils.logging import SecurityLogger, ErrorLogger, logger
from app.utils.common import ValidationUtils, DateTimeUtils


class UserService:
    """
    ユーザー管理サービス
    
    ユーザーに関する全てのビジネスロジックを担当します。
    データベース操作、バリデーション、セキュリティチェックなどを統合的に管理します。
    
    属性:
        db: データベースセッション（AsyncSession）
    """
    def __init__(self, db: AsyncSession):
        """
        ユーザーサービスの初期化
        
        引数:
            db: データベースセッション
            
        戻り値:
            UserService: ユーザーサービスインスタンス
        """
        self.db = db

    async def get_by_id(self, user_id: Union[int, UUID, str]) -> Optional[User]:
        """
        ユーザーIDでユーザー情報を取得
        
        引数:
            user_id: ユーザーの一意識別子（UUID、整数、または文字列）
            
        戻り値:
            User: ユーザー情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            # UUID文字列の場合はUUIDオブジェクトに変換
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    logger.warning(f"無効なユーザーID形式: {user_id}")
                    return None
            
            if not user_id:
                logger.warning(f"無効なユーザーID: {user_id}")
                return None
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.id == user_id)
                .where(User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()
            
            if user:
                # ユーザー取得成功はDEBUGレベル（通常の認証フローでは不要なログ）
                logger.debug(f"ユーザー取得成功: ID {user_id}")
            else:
                # ユーザー未発見はWARNINGレベル（異常系のため）
                logger.warning(f"ユーザー未発見: ID {user_id}")
                
            return user
        except Exception as e:
            logger.error(f"ユーザー取得エラー: {str(e)}")
            raise

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        メールアドレスでユーザー情報を取得
        
        引数:
            email: ユーザーのメールアドレス
            
        戻り値:
            User: ユーザー情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            if not email or not ValidationUtils.validate_email(email):
                logger.warning(f"無効なメールアドレス: {email}")
                return None
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.email == email)
                .where(User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(
                    f"ユーザー操作: user_id={user.id}, action=get_by_email, resource=user, tenant_id={user.tenant_id}"
                )
            else:
                logger.info(f"ユーザー未発見: メール {email}")
                
            return user
        except Exception as e:
            ErrorLogger.log_exception(e, {"operation": "get_by_email", "email": email})
            raise

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        ユーザー名でユーザー情報を取得
        
        引数:
            username: ユーザー名
            
        戻り値:
            User: ユーザー情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            if not username or len(username) < 3 or len(username) > 20:
                logger.warning(f"無効なユーザー名: {username}")
                return None
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.username == username)
                .where(User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(
                    f"ユーザー操作: user_id={user.id}, action=get_by_username, resource=user, tenant_id={user.tenant_id}"
                )
            else:
                logger.info(f"ユーザー未発見: ユーザー名 {username}")
                
            return user
        except Exception as e:
            ErrorLogger.log_exception(e, {"operation": "get_by_username", "username": username})
            raise

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        全ユーザー一覧を取得（ページネーション対応）
        
        引数:
            skip: スキップする件数
            limit: 取得する最大件数
            
        戻り値:
            List[User]: ユーザー一覧
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            if skip < 0 or limit <= 0 or limit > 1000:
                raise ValueError("無効なページネーションパラメータ")
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.deleted_at.is_(None))
                .offset(skip)
                .limit(limit)
            )
            users = result.scalars().all()
            
            logger.info(f"ユーザー一覧取得成功: {len(users)}件")
            return users
        except Exception as e:
            logger.error(f"ユーザー一覧取得エラー: {str(e)}")
            raise

    async def get_users_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """
        テナントIDでユーザー一覧を取得
        
        引数:
            tenant_id: テナントID
            skip: スキップする件数
            limit: 取得する最大件数
            
        戻り値:
            List[User]: テナントに所属するユーザー一覧
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            if not tenant_id:
                raise ValueError("テナントIDが必須です")
                
            if skip < 0 or limit <= 0 or limit > 1000:
                raise ValueError("無効なページネーションパラメータ")
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.tenant_id == tenant_id)
                .where(User.deleted_at.is_(None))
                .offset(skip)
                .limit(limit)
            )
            users = result.scalars().all()
            
            logger.info(f"テナントユーザー一覧取得成功: テナント {tenant_id}, {len(users)}件")
            return users
        except Exception as e:
            logger.error(f"テナントユーザー一覧取得エラー: {str(e)}")
            raise

    async def create_user(self, user_data: UserCreate) -> User:
        """
        新規ユーザーを作成
        
        引数:
            user_data: ユーザー作成データ
            
        戻り値:
            User: 作成されたユーザー情報
            
        例外:
            EmailAlreadyExistsError: メールアドレス重複
            UsernameAlreadyExistsError: ユーザー名重複
            ValidationError: バリデーションエラー
        """
        try:
            # 入力値のバリデーション
            if not ValidationUtils.validate_email(user_data.email):
                raise ValidationError("無効なメールアドレス形式です")
                
            password_validation = ValidationUtils.validate_password_strength(user_data.password)
            if not password_validation['is_valid']:
                raise ValidationError("パスワードは8文字以上で、大文字、小文字、数字を含む必要があります")
                
            if not user_data.username or len(user_data.username) < 3 or len(user_data.username) > 20:
                raise ValidationError("ユーザー名は3-20文字の英数字とアンダースコアのみ使用可能です")
            
            # 重複チェック（削除済みは除外、deleted_at IS NULLのみチェック）
            from sqlalchemy import or_
            existing_user = await self.db.execute(
                select(User).where(
                    or_(
                        User.email == user_data.email,
                        User.username == user_data.username
                    )
                ).where(User.deleted_at.is_(None))
            )
            existing = existing_user.scalar_one_or_none()
            
            if existing:
                # 削除済み（deleted_at IS NOT NULL）の場合は重複として扱わない（新規作成可能）
                # deleted_at IS NULL AND is_active = False の場合は再有効化
                if not existing.is_active:
                    existing.email = user_data.email
                    existing.username = user_data.username
                    existing.hashed_password = get_password_hash(user_data.password)
                    existing.role = user_data.role
                    existing.tenant_id = user_data.tenant_id
                    existing.is_active = True
                    existing.is_verified = False
                    existing.deleted_at = None  # 念のためNULLに設定
                    await self.db.commit()
                    await self.db.refresh(existing)
                    logger.info(
                        f"ユーザー操作: user_id={existing.id}, action=reactivate_user, resource=user, tenant_id={existing.tenant_id}"
                    )
                    return existing
                # アクティブユーザーの重複はエラー
                if existing.email == user_data.email:
                    SecurityLogger.log_suspicious_activity(
                        None,
                        "duplicate_email_registration",
                        {"email": user_data.email}
                    )
                    raise EmailAlreadyExistsError()
                else:
                    SecurityLogger.log_suspicious_activity(
                        None,
                        "duplicate_username_registration",
                        {"username": user_data.username}
                    )
                    raise UsernameAlreadyExistsError()
            
            # パスワードのハッシュ化
            hashed_password = get_password_hash(user_data.password)
            
            # ユーザー作成
            user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                role=user_data.role,
                tenant_id=user_data.tenant_id,
                is_active=True,
                is_verified=False
            )
            
            self.db.add(user)
            # 永続化
            await self.db.flush()  # ID採番
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(
                f"ユーザー操作: user_id={user.id}, action=create_user, resource=user, tenant_id={user.tenant_id}"
            )
            return user
            
        except (EmailAlreadyExistsError, UsernameAlreadyExistsError, ValidationError):
            raise
        except Exception as e:
            await self.db.rollback()
            ErrorLogger.log_exception(e, {"operation": "create_user"})
            raise

    async def update_user(self, user_id: Union[int, UUID, str], user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(user, ['tenant'])
        return user

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login time"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.last_login_at = DateTimeUtils.now()
        await self.db.commit()
        return True

    async def delete_user(self, user_id: Union[int, UUID, str]) -> bool:
        """Delete user (soft delete by setting deleted_at and is_active=False)"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.deleted_at = DateTimeUtils.now()
        user.is_active = False
        await self.db.commit()
        return True

    async def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete user from database"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def change_user_role(self, user_id: int, new_role: UserRole) -> bool:
        """Change user role (admin only)"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.role = new_role
        await self.db.commit()
        return True

    async def activate_user(self, user_id: int) -> bool:
        """Activate user account"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_active = True
        await self.db.commit()
        return True

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        await self.db.commit()
        return True

    async def verify_user(self, user_id: int) -> bool:
        """Mark user as verified"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_verified = True
        await self.db.commit()
        return True
