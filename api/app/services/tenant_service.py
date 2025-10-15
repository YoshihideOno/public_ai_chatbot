"""
テナント管理サービス

このファイルはテナント（顧客企業）のビジネスロジックを実装します。
テナントのCRUD操作、設定管理、APIキー管理、統計情報の取得などの機能を提供します。

主な機能:
- テナントの作成・更新・削除
- APIキーの生成・管理
- テナント設定の管理
- 統計情報の取得
- 埋め込みコードの生成
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantStats, TenantSettings,
    TenantApiKey, TenantEmbedSnippet
)
from app.services.user_service import UserService
from app.utils.common import StringUtils, ValidationUtils
from app.utils.logging import BusinessLogger, SecurityLogger


class TenantService:
    """
    テナント管理サービス
    
    テナントに関する全てのビジネスロジックを担当します。
    データベース操作、バリデーション、セキュリティチェックなどを統合的に管理します。
    
    属性:
        db: データベースセッション（AsyncSession）
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """
        テナントIDでテナント情報を取得
        
        引数:
            tenant_id: テナントの一意識別子
            
        戻り値:
            Tenant: テナント情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            result = await self.db.execute(
                select(Tenant)
                .options(selectinload(Tenant.users))
                .where(Tenant.id == tenant_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            BusinessLogger.error(f"テナント取得エラー: {str(e)}")
            raise

    async def get_by_domain(self, domain: str) -> Optional[Tenant]:
        """
        ドメイン名でテナント情報を取得
        
        引数:
            domain: テナントのドメイン名
            
        戻り値:
            Tenant: テナント情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            # ドメイン名のバリデーション
            if not ValidationUtils.is_valid_domain(domain):
                raise ValueError("無効なドメイン名です")
                
            result = await self.db.execute(
                select(Tenant)
                .options(selectinload(Tenant.users))
                .where(Tenant.domain == domain)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            BusinessLogger.error(f"ドメイン検索エラー: {str(e)}")
            raise

    async def get_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """
        APIキーでテナント情報を取得
        
        引数:
            api_key: テナントのAPIキー
            
        戻り値:
            Tenant: テナント情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            # APIキーのバリデーション
            if not ValidationUtils.is_valid_api_key(api_key):
                SecurityLogger.warning(f"無効なAPIキー形式: {api_key[:10]}...")
                return None
                
            result = await self.db.execute(
                select(Tenant)
                .options(selectinload(Tenant.users))
                .where(Tenant.api_key == api_key)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            SecurityLogger.error(f"APIキー検索エラー: {str(e)}")
            raise

    async def get_all_tenants(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Tenant]:
        """全テナント取得（ページネーション対応）"""
        query = select(Tenant).options(selectinload(Tenant.users))
        
        if status:
            query = query.where(Tenant.status == status)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """テナント作成"""
        # ドメインの重複チェック
        existing_tenant = await self.get_by_domain(tenant_data.domain)
        if existing_tenant:
            raise ValueError("このドメインは既に使用されています")
        
        # APIキー生成
        api_key = StringUtils.generate_api_key("pk_live")
        
        # テナント作成
        db_tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_data.name,
            domain=tenant_data.domain,
            plan=tenant_data.plan,
            status=tenant_data.status,
            api_key=api_key,
            settings=tenant_data.settings
        )
        
        self.db.add(db_tenant)
        await self.db.commit()
        await self.db.refresh(db_tenant)
        
        # 管理者ユーザー作成
        if tenant_data.admin_user:
            user_service = UserService(self.db)
            admin_user_data = {
                "email": tenant_data.admin_user["email"],
                "username": tenant_data.admin_user["username"],
                "password": tenant_data.admin_user["password"],
                "role": UserRole.TENANT_ADMIN,
                "tenant_id": db_tenant.id
            }
            
            admin_user = await user_service.create_user(admin_user_data)
            
            BusinessLogger.log_tenant_action(
                db_tenant.id,
                "tenant_created",
                {
                    "name": db_tenant.name,
                    "domain": db_tenant.domain,
                    "plan": db_tenant.plan,
                    "admin_user_id": admin_user.id
                }
            )
        
        return db_tenant

    async def update_tenant(self, tenant_id: str, tenant_update: TenantUpdate) -> Optional[Tenant]:
        """テナント更新"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        # ドメイン変更時の重複チェック
        if tenant_update.domain and tenant_update.domain != tenant.domain:
            existing_tenant = await self.get_by_domain(tenant_update.domain)
            if existing_tenant:
                raise ValueError("このドメインは既に使用されています")
        
        update_data = tenant_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        tenant.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "tenant_updated",
            update_data
        )
        
        return tenant

    async def delete_tenant(self, tenant_id: str) -> bool:
        """テナント削除（ソフトデリート）"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        tenant.status = "DELETED"
        tenant.deleted_at = datetime.utcnow()
        
        await self.db.commit()
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "tenant_deleted",
            {"name": tenant.name, "domain": tenant.domain}
        )
        
        return True

    async def regenerate_api_key(self, tenant_id: str) -> Optional[str]:
        """APIキー再発行"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        new_api_key = StringUtils.generate_api_key("pk_live")
        tenant.api_key = new_api_key
        tenant.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        SecurityLogger.log_suspicious_activity(
            None,
            "api_key_regenerated",
            {"tenant_id": tenant_id, "old_key": tenant.api_key[:10] + "..."},
            tenant_id=tenant_id
        )
        
        return new_api_key

    async def get_tenant_stats(self, tenant_id: str) -> Optional[TenantStats]:
        """テナント統計取得"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        # ユーザー統計
        users_result = await self.db.execute(
            select(func.count(User.id))
            .where(User.tenant_id == tenant_id)
        )
        total_users = users_result.scalar() or 0
        
        active_users_result = await self.db.execute(
            select(func.count(User.id))
            .where(User.tenant_id == tenant_id, User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0
        
        # TODO: ファイル、チャンク、会話、ストレージ統計を実装
        # 現在は仮の値を返す
        
        return TenantStats(
            total_users=total_users,
            active_users=active_users,
            total_files=0,  # TODO: 実装
            total_chunks=0,  # TODO: 実装
            total_conversations=0,  # TODO: 実装
            storage_used_mb=0.0,  # TODO: 実装
            queries_this_month=0,  # TODO: 実装
            last_activity=None  # TODO: 実装
        )

    async def update_tenant_settings(self, tenant_id: str, settings: TenantSettings) -> bool:
        """テナント設定更新"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        tenant.settings = settings.dict()
        tenant.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "settings_updated",
            {"settings": settings.dict()}
        )
        
        return True

    async def get_tenant_users(self, tenant_id: str) -> List[User]:
        """テナントのユーザー一覧取得"""
        result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def add_user_to_tenant(self, tenant_id: str, user_id: int) -> bool:
        """テナントにユーザー追加"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        user_service = UserService(self.db)
        user = await user_service.get_by_id(user_id)
        if not user:
            return False
        
        user.tenant_id = tenant_id
        await self.db.commit()
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "user_added",
            {"user_id": user_id, "user_email": user.email}
        )
        
        return True

    async def remove_user_from_tenant(self, tenant_id: str, user_id: int) -> bool:
        """テナントからユーザー削除"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        user_service = UserService(self.db)
        user = await user_service.get_by_id(user_id)
        if not user or user.tenant_id != tenant_id:
            return False
        
        user.tenant_id = None
        await self.db.commit()
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "user_removed",
            {"user_id": user_id, "user_email": user.email}
        )
        
        return True

    async def generate_embed_snippet(self, tenant_id: str) -> Optional[TenantEmbedSnippet]:
        """埋め込みスニペット生成"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        snippet = f"""
<script>
  (function(w,d,s,o,f,js,fjs){{
    w['RAGChatWidget']=o;w[o]=w[o]||function(){{(w[o].q=w[o].q||[]).push(arguments)}};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }}(window,document,'script','ragChat','https://cdn.rag-chatbot.com/widget.js'));
  
  ragChat('init', {{
    tenantId: '{tenant.id}',
    apiKey: '{tenant.api_key}',
    theme: 'light',
    position: 'bottom-right'
  }});
</script>
        """.strip()
        
        return TenantEmbedSnippet(
            snippet=snippet,
            tenant_id=tenant.id,
            api_key=tenant.api_key
        )

    async def validate_tenant_access(self, tenant_id: str, user_id: int) -> bool:
        """テナントアクセス権限チェック"""
        user_service = UserService(self.db)
        user = await user_service.get_by_id(user_id)
        
        if not user:
            return False
        
        # Platform Adminは全テナントにアクセス可能
        if user.role == UserRole.PLATFORM_ADMIN:
            return True
        
        # その他のユーザーは自分のテナントのみ
        return user.tenant_id == tenant_id

    async def get_tenant_usage_summary(self, tenant_id: str) -> Dict[str, Any]:
        """テナント使用量サマリ"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return {}
        
        # TODO: 実際の使用量データを取得
        # 現在は仮の値を返す
        
        return {
            "queries_this_month": 0,
            "queries_limit": 1000,
            "storage_used_mb": 0.0,
            "storage_limit_mb": 100.0,
            "active_users": 0,
            "total_users": 0,
            "last_activity": None
        }
