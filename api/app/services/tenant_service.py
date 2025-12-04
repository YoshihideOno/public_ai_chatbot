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
from datetime import datetime, timedelta
from app.core.constants import ReminderSettings, SystemMessages
import uuid
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantStats, TenantSettings,
    TenantApiKey, TenantEmbedSnippet
)
from app.services.user_service import UserService
from app.utils.common import StringUtils, ValidationUtils, DateTimeUtils
from app.utils.logging import BusinessLogger, SecurityLogger, logger


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
            logger.error(f"テナント取得エラー: {str(e)}")
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
            result = await self.db.execute(
                select(Tenant).where(Tenant.domain == domain)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"ドメイン検索エラー: {str(e)}")
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
            # APIキーの簡易バリデーション（形式チェックは長さのみ）
            if not api_key or len(api_key.strip()) < 16:
                SecurityLogger.warning(f"無効なAPIキー形式: {api_key[:10]}...")
                return None
                
            result = await self.db.execute(
                select(Tenant)
                .options(selectinload(Tenant.users))
                .where(Tenant.api_key == api_key)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                "APIキー検索エラー",
                error=str(e),
                api_key_prefix=api_key[:10] + "..." if api_key else None
            )
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
        # テナント作成
        db_tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_data.name,
            domain=tenant_data.domain,
            plan=tenant_data.plan,
            status=tenant_data.status,
            settings=tenant_data.settings
        )
        
        self.db.add(db_tenant)
        # トランザクション内ではcommitしない
        await self.db.flush()  # flushでIDを取得
        await self.db.refresh(db_tenant)
        
        return db_tenant

    async def update_tenant(self, tenant_id: str, tenant_update: TenantUpdate) -> Optional[Tenant]:
        """テナント更新"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        # ドメイン変更時のバリデーション（重複チェックは削除）
        
        # exclude_unset=Trueで明示的に設定されたフィールドのみを取得
        # exclude_none=FalseでNone値も含める（allowed_widget_originsをNoneに設定する場合に対応）
        update_data = tenant_update.dict(exclude_unset=True, exclude_none=False)
        
        # Pydantic v2のmodel_fields_setを使って明示的に設定されたフィールドを確認
        # Pydantic v1とv2の互換性を考慮
        if hasattr(tenant_update, 'model_fields_set'):
            # Pydantic v2の場合
            fields_set = tenant_update.model_fields_set
        elif hasattr(tenant_update, '__fields_set__'):
            # Pydantic v1の場合（__fields_set__を使用）
            fields_set = tenant_update.__fields_set__
        else:
            # フォールバック: update_dataのキーから推測
            fields_set = set(update_data.keys())
        
        # settingsが含まれている場合は、既存の設定とマージ
        if 'settings' in update_data:
            current_settings = dict(tenant.settings) if tenant.settings else {}
            new_settings = update_data.pop('settings')
            if new_settings is not None:
                # 既存の設定とマージ（部分更新）
                current_settings.update(new_settings)
                # None値のキーを削除
                # ただし、default_modelとembedding_modelはNone値でも保持（未選択状態を明示的に保存）
                for key in list(current_settings.keys()):
                    if current_settings[key] is None:
                        # default_modelとembedding_modelはNone値でも保持
                        if key not in ('default_model', 'embedding_model'):
                            del current_settings[key]
                tenant.settings = current_settings
        
        # allowed_widget_originsを明示的に処理（Pydanticのexclude_unsetの動作に依存せず確実に更新）
        # fields_setに含まれている場合、またはupdate_dataに含まれている場合は更新
        if 'allowed_widget_origins' in fields_set or 'allowed_widget_origins' in update_data:
            # 値が明示的に送られた場合（Noneでも空文字列でも）は更新
            new_value = update_data.pop('allowed_widget_origins', None)
            # fields_setに含まれているがupdate_dataに含まれていない場合（None値の場合）も処理
            if 'allowed_widget_origins' in fields_set and 'allowed_widget_origins' not in update_data:
                new_value = tenant_update.allowed_widget_origins
            
            tenant.allowed_widget_origins = new_value
        
        # その他のフィールドを更新
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        tenant.updated_at = DateTimeUtils.now()
        
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
        tenant.deleted_at = DateTimeUtils.now()
        
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
        tenant.updated_at = DateTimeUtils.now()
        
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
        """
        テナント設定更新
        
        部分更新をサポートします。指定されたフィールドのみを更新し、
        None値のフィールドは既存の設定から削除します。
        """
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        # 既存の設定を取得（空の場合は空辞書）
        current_settings = tenant.settings if tenant.settings else {}
        
        # 指定されたフィールドのみを更新（exclude_unset=Trueでデフォルト値で埋められないようにする）
        updated_settings = settings.dict(exclude_unset=True, exclude_none=False)
        
        # 既存の設定とマージ
        current_settings.update(updated_settings)
        
        # None値（未選択の場合）はキーを削除
        # ただし、default_modelとembedding_modelはNone値でも保持（未選択状態を明示的に保存）
        for key in list(current_settings.keys()):
            if current_settings[key] is None:
                # default_modelとembedding_modelはNone値でも保持
                if key not in ('default_model', 'embedding_model'):
                    del current_settings[key]
        
        tenant.settings = current_settings
        tenant.updated_at = DateTimeUtils.now()
        
        await self.db.commit()
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "settings_updated",
            {"settings": current_settings}
        )
        
        return True

    async def update_tenant_settings_dict(self, tenant_id: str, settings: Dict[str, Any]) -> bool:
        """
        テナント設定更新（Dict形式）
        
        部分更新をサポートします。指定されたフィールドのみを更新し、
        None値のフィールドは既存の設定から削除します。
        """
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        # 既存の設定を取得（空の場合は空辞書）
        # 新しい辞書オブジェクトとして作成（SQLAlchemyの変更検知のため）
        current_settings = dict(tenant.settings) if tenant.settings else {}
        
        # 送信されたフィールドのみを更新
        current_settings.update(settings)
        
        # None値（未選択の場合）はキーを削除
        # ただし、default_modelとembedding_modelはNone値でも保持（未選択状態を明示的に保存）
        for key in list(current_settings.keys()):
            if current_settings[key] is None:
                # default_modelとembedding_modelはNone値でも保持
                if key not in ('default_model', 'embedding_model'):
                    del current_settings[key]
        
        # 新しい辞書オブジェクトとして割り当て（SQLAlchemyが変更を検知できるように）
        tenant.settings = current_settings
        tenant.updated_at = DateTimeUtils.now()
        
        # 明示的にフラッシュして変更を確認
        await self.db.flush()
        await self.db.commit()
        
        BusinessLogger.log_tenant_action(
            tenant_id,
            "settings_updated",
            {"settings": current_settings}
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
        from app.utils.logging import logger
        from app.core.config import settings
        
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            logger.error(f"テナントが見つかりません: tenant_id={tenant_id}")
            return None
        
        # APIキーが存在しない場合はエラー
        if not tenant.api_key:
            logger.error(f"テナントのAPIキーが設定されていません: tenant_id={tenant_id}")
            # APIキーを生成
            new_api_key = await self.regenerate_api_key(tenant_id)
            if not new_api_key:
                logger.error(f"APIキーの生成に失敗しました: tenant_id={tenant_id}")
                return None
            # テナントを再取得
            tenant = await self.get_by_id(tenant_id)
            if not tenant or not tenant.api_key:
                logger.error(f"APIキー生成後のテナント取得に失敗: tenant_id={tenant_id}")
                return None
        
        # ウィジェットCDN URLを取得（環境変数から、なければデフォルト値）
        widget_cdn_url = settings.WIDGET_CDN_URL or 'https://cdn.rag-chatbot.com/widget.js'
        
        # APIベースURLを取得（環境変数から、なければAPP_URLから構築）
        if settings.API_BASE_URL:
            api_base_url = settings.API_BASE_URL
        elif settings.APP_URL:
            # APP_URLからAPIベースURLを構築
            api_base_url = f"{settings.APP_URL.rstrip('/')}/api/v1"
        else:
            # フォールバック: 相対パスを使用
            api_base_url = '/api/v1'
            logger.warning("WIDGET_CDN_URLとAPP_URLが設定されていないため、相対パスを使用します")
        
        snippet = f"""
<script>
  (function(w,d,s,o,f,js,fjs){{
    w['RAGChatWidget']=o;w[o]=w[o]||function(){{(w[o].q=w[o].q||[]).push(arguments)}};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }}(window,document,'script','ragChat','{widget_cdn_url}'));
  
  ragChat('init', {{
    tenantId: '{tenant.id}',
    apiKey: '{tenant.api_key}',
    apiBaseUrl: '{api_base_url}',
    theme: 'light',
    position: 'bottom-right'
  }});
</script>
        """.strip()
        
        return TenantEmbedSnippet(
            snippet=snippet,
            tenant_id=str(tenant.id),
            api_key=tenant.api_key
        )

    async def validate_tenant_access(self, tenant_id: str, user_id) -> bool:
        """テナントアクセス権限チェック"""
        from uuid import UUID
        
        user_service = UserService(self.db)
        # user_idがUUIDの場合はそのまま、文字列の場合はUUIDに変換
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                logger.error(f"無効なuser_id形式: {user_id}")
                return False
        
        user = await user_service.get_by_id(user_id)
        
        if not user:
            return False
        
        # Platform Adminは全テナントにアクセス可能
        if user.role == UserRole.PLATFORM_ADMIN:
            return True
        
        # その他のユーザーは自分のテナントのみ
        return str(user.tenant_id) == str(tenant_id)

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
    
    async def update_knowledge_registration_date(self, tenant_id: str) -> bool:
        """
        ナレッジ登録日時を更新
        
        初回ナレッジ登録時に呼び出されます。
        
        引数:
            tenant_id: テナントID
        戻り値:
            bool: 更新成功時True
        """
        try:
            tenant = await self.get_by_id(tenant_id)
            if not tenant:
                return False
            
            # 既に登録日時が設定されている場合は更新しない
            if tenant.knowledge_registered_at:
                return True
            
            # ナレッジ登録日時を現在時刻に設定
            tenant.knowledge_registered_at = DateTimeUtils.now()
            await self.db.commit()
            
            BusinessLogger.log_user_action(
                tenant_id,
                "knowledge_registered",
                "tenant",
                tenant_id=tenant_id
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"ナレッジ登録日時更新エラー: {str(e)}")
            raise
    
    async def check_trial_period_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        お試し利用期間の状態をチェック
        
        引数:
            tenant_id: テナントID
        戻り値:
            Dict[str, Any]: 期間状態情報
                - is_trial_active: お試し利用中かどうか
                - is_expired: 期間満了かどうか
                - days_remaining: 残り日数
                - trial_end_date: お試し利用終了日
                - message: 状態メッセージ
        """
        try:
            tenant = await self.get_by_id(tenant_id)
            if not tenant:
                return {
                    "is_trial_active": False,
                    "is_expired": True,
                    "days_remaining": 0,
                    "trial_end_date": None,
                    "message": "テナントが見つかりません"
                }
            
            # ナレッジ登録日時が設定されていない場合
            if not tenant.knowledge_registered_at:
                return {
                    "is_trial_active": False,
                    "is_expired": False,
                    "days_remaining": None,
                    "trial_end_date": None,
                    "message": "ナレッジが登録されていません"
                }
            
            # お試し利用期間の計算
            trial_period = ReminderSettings.get_trial_period()
            trial_end_date = tenant.knowledge_registered_at + trial_period
            current_date = DateTimeUtils.now()
            
            # 期間満了チェック
            is_expired = current_date > trial_end_date
            days_remaining = (trial_end_date - current_date).days if not is_expired else 0
            
            # サブスクリプション状態のチェック（BillingInfoから取得）
            # TODO: BillingInfoサービスと連携してサブスクリプション状態を確認
            has_active_subscription = False  # 仮の値
            
            # お試し利用中かどうかの判定
            is_trial_active = not is_expired and not has_active_subscription
            
            # メッセージの生成
            if has_active_subscription:
                message = "サブスクリプション契約中です"
            elif is_expired:
                message = SystemMessages.TRIAL_EXPIRED_MESSAGE
            elif days_remaining <= 0:
                message = SystemMessages.TRIAL_EXPIRED_MESSAGE
            else:
                message = f"お試し利用中（残り{days_remaining}日）"
            
            return {
                "is_trial_active": is_trial_active,
                "is_expired": is_expired,
                "days_remaining": max(0, days_remaining),
                "trial_end_date": trial_end_date,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"お試し利用期間チェックエラー: {str(e)}")
            return {
                "is_trial_active": False,
                "is_expired": True,
                "days_remaining": 0,
                "trial_end_date": None,
                "message": "期間チェックに失敗しました"
            }
    
    async def can_use_service(self, tenant_id: str) -> bool:
        """
        サービス利用可能かチェック
        
        お試し利用期間内またはサブスクリプション契約中の場合にTrueを返します。
        
        引数:
            tenant_id: テナントID
        戻り値:
            bool: サービス利用可能な場合True
        """
        try:
            status_info = await self.check_trial_period_status(tenant_id)
            
            # お試し利用中またはサブスクリプション契約中の場合
            return status_info["is_trial_active"] or not status_info["is_expired"]
            
        except Exception as e:
            logger.error(f"サービス利用可能性チェックエラー: {str(e)}")
            return False
