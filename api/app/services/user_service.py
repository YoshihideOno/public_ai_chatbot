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
from typing import Optional, List
from datetime import datetime
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import (
    UserNotFoundError, EmailAlreadyExistsError, UsernameAlreadyExistsError,
    ValidationError, BusinessLogicError
)
from app.utils.logging import BusinessLogger, SecurityLogger
from app.utils.common import ValidationUtils


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

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        ユーザーIDでユーザー情報を取得
        
        引数:
            user_id: ユーザーの一意識別子
            
        戻り値:
            User: ユーザー情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            if not user_id or user_id <= 0:
                BusinessLogger.warning(f"無効なユーザーID: {user_id}")
                return None
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                BusinessLogger.info(f"ユーザー取得成功: ID {user_id}")
            else:
                BusinessLogger.info(f"ユーザー未発見: ID {user_id}")
                
            return user
        except Exception as e:
            BusinessLogger.error(f"ユーザー取得エラー: {str(e)}")
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
            if not email or not ValidationUtils.is_valid_email(email):
                BusinessLogger.warning(f"無効なメールアドレス: {email}")
                return None
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if user:
                BusinessLogger.info(f"ユーザー取得成功: メール {email}")
            else:
                BusinessLogger.info(f"ユーザー未発見: メール {email}")
                
            return user
        except Exception as e:
            BusinessLogger.error(f"メール検索エラー: {str(e)}")
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
            if not username or not ValidationUtils.is_valid_username(username):
                BusinessLogger.warning(f"無効なユーザー名: {username}")
                return None
                
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.tenant))
                .where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                BusinessLogger.info(f"ユーザー取得成功: ユーザー名 {username}")
            else:
                BusinessLogger.info(f"ユーザー未発見: ユーザー名 {username}")
                
            return user
        except Exception as e:
            BusinessLogger.error(f"ユーザー名検索エラー: {str(e)}")
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
                .offset(skip)
                .limit(limit)
            )
            users = result.scalars().all()
            
            BusinessLogger.info(f"ユーザー一覧取得成功: {len(users)}件")
            return users
        except Exception as e:
            BusinessLogger.error(f"ユーザー一覧取得エラー: {str(e)}")
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
                .offset(skip)
                .limit(limit)
            )
            users = result.scalars().all()
            
            BusinessLogger.info(f"テナントユーザー一覧取得成功: テナント {tenant_id}, {len(users)}件")
            return users
        except Exception as e:
            BusinessLogger.error(f"テナントユーザー一覧取得エラー: {str(e)}")
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
            if not ValidationUtils.is_valid_email(user_data.email):
                raise ValidationError("無効なメールアドレス形式です")
                
            if not ValidationUtils.is_valid_password(user_data.password):
                raise ValidationError("パスワードは8文字以上で、英数字と記号を含む必要があります")
                
            if not ValidationUtils.is_valid_username(user_data.username):
                raise ValidationError("ユーザー名は3-20文字の英数字とアンダースコアのみ使用可能です")
            
            # 重複チェック
            existing_email = await self.get_by_email(user_data.email)
            if existing_email:
                SecurityLogger.warning(f"メールアドレス重複試行: {user_data.email}")
                raise EmailAlreadyExistsError()
                
            existing_username = await self.get_by_username(user_data.username)
            if existing_username:
                SecurityLogger.warning(f"ユーザー名重複試行: {user_data.username}")
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
            await self.db.commit()
            await self.db.refresh(user)
            
            BusinessLogger.info(f"新規ユーザー作成完了: {user.email}")
            return user
            
        except (EmailAlreadyExistsError, UsernameAlreadyExistsError, ValidationError):
            raise
        except Exception as e:
            await self.db.rollback()
            BusinessLogger.error(f"ユーザー作成エラー: {str(e)}")
            raise
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=user_data.role,
            tenant_id=user_data.tenant_id,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        # Load tenant information
        await self.db.refresh(db_user, ['tenant'])
        return db_user

    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_update.dict(exclude_unset=True)
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

        user.last_login_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete by setting is_active=False)"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

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
