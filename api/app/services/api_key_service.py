"""
APIキー管理サービス

このファイルはAPIキーに関するビジネスロジックを実装します。
APIキーのCRUD操作、暗号化・復号化、バリデーションなどの機能を提供します。

主な機能:
- APIキーの作成・更新・削除
- APIキーの暗号化・復号化
- プロバイダー・モデル検証
- テナント毎のAPIキー管理
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse
from app.core.exceptions import (
    ApiKeyNotFoundError, ValidationError, BusinessLogicError
)
from app.utils.logging import SecurityLogger, ErrorLogger, logger
from app.core.config import settings
import base64


class ApiKeyService:
    """
    APIキー管理サービス
    
    APIキーに関する全てのビジネスロジックを担当します。
    データベース操作、暗号化、バリデーション、セキュリティチェックなどを統合的に管理します。
    
    属性:
        db: データベースセッション（AsyncSession）
        cipher: 暗号化オブジェクト（Fernet）
    """
    
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        引数:
            db: データベースセッション
        """
        self.db = db
        # 暗号化キーの生成（本番環境では環境変数から取得）
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        self.cipher = Fernet(base64.urlsafe_b64encode(key))
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """
        APIキーを暗号化
        
        引数:
            api_key: 平文のAPIキー
        戻り値:
            str: 暗号化されたAPIキー
        """
        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            ErrorLogger.error(f"APIキー暗号化エラー: {str(e)}")
            raise BusinessLogicError("APIキーの暗号化に失敗しました")
    
    def _decrypt_api_key(self, encrypted_api_key: str) -> str:
        """
        APIキーを復号化
        
        引数:
            encrypted_api_key: 暗号化されたAPIキー
        戻り値:
            str: 平文のAPIキー
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_api_key.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            ErrorLogger.error(f"APIキー復号化エラー: {str(e)}")
            raise BusinessLogicError("APIキーの復号化に失敗しました")
    
    async def create_api_key(self, tenant_id: str, api_key_data: ApiKeyCreate) -> ApiKey:
        """
        APIキー作成
        
        引数:
            tenant_id: テナントID
            api_key_data: APIキー作成データ
        戻り値:
            ApiKey: 作成されたAPIキー
        """
        try:
            # 既存のAPIキーをチェック（同じプロバイダー）
            existing_query = select(ApiKey).where(
                and_(
                    ApiKey.tenant_id == tenant_id,
                    ApiKey.provider == api_key_data.provider,
                    ApiKey.is_active == True
                )
            )
            result = await self.db.execute(existing_query)
            existing_api_key = result.scalar_one_or_none()
            
            if existing_api_key:
                raise BusinessLogicError(f"プロバイダー {api_key_data.provider} のAPIキーは既に登録されています")
            
            # APIキーを暗号化
            encrypted_api_key = self._encrypt_api_key(api_key_data.api_key)
            
            # APIキー作成
            db_api_key = ApiKey(
                tenant_id=tenant_id,
                provider=api_key_data.provider,
                api_key=encrypted_api_key,
                model=api_key_data.model,
                is_active=True
            )
            
            self.db.add(db_api_key)
            await self.db.commit()
            await self.db.refresh(db_api_key)
            
            SecurityLogger.log_user_action(
                tenant_id,
                "create_api_key",
                "api_key",
                {"provider": api_key_data.provider, "model": api_key_data.model}
            )
            
            logger.info(f"APIキー作成完了: tenant={tenant_id}, provider={api_key_data.provider}")
            return db_api_key
            
        except Exception as e:
            await self.db.rollback()
            ErrorLogger.error(f"APIキー作成エラー: {str(e)}")
            raise
    
    async def get_api_key(self, api_key_id: str, tenant_id: str) -> Optional[ApiKey]:
        """
        APIキー取得
        
        引数:
            api_key_id: APIキーID
            tenant_id: テナントID
        戻り値:
            Optional[ApiKey]: APIキー情報（存在しない場合はNone）
        """
        try:
            query = select(ApiKey).where(
                and_(
                    ApiKey.id == api_key_id,
                    ApiKey.tenant_id == tenant_id
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            ErrorLogger.error(f"APIキー取得エラー: {str(e)}")
            raise
    
    async def get_api_keys_by_tenant(self, tenant_id: str) -> List[ApiKey]:
        """
        テナントのAPIキー一覧取得
        
        引数:
            tenant_id: テナントID
        戻り値:
            List[ApiKey]: APIキー一覧
        """
        try:
            query = select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at.desc())
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            ErrorLogger.error(f"APIキー一覧取得エラー: {str(e)}")
            raise
    
    async def update_api_key(self, api_key_id: str, tenant_id: str, update_data: ApiKeyUpdate) -> Optional[ApiKey]:
        """
        APIキー更新
        
        引数:
            api_key_id: APIキーID
            tenant_id: テナントID
            update_data: 更新データ
        戻り値:
            Optional[ApiKey]: 更新されたAPIキー（存在しない場合はNone）
        """
        try:
            # APIキー取得
            api_key = await self.get_api_key(api_key_id, tenant_id)
            if not api_key:
                return None
            
            # 更新データの適用
            if update_data.api_key is not None:
                api_key.api_key = self._encrypt_api_key(update_data.api_key)
            if update_data.model is not None:
                api_key.model = update_data.model
            if update_data.is_active is not None:
                api_key.is_active = update_data.is_active
            
            api_key.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(api_key)
            
            SecurityLogger.log_user_action(
                tenant_id,
                "update_api_key",
                "api_key",
                {"api_key_id": api_key_id}
            )
            
            logger.info(f"APIキー更新完了: tenant={tenant_id}, api_key_id={api_key_id}")
            return api_key
            
        except Exception as e:
            await self.db.rollback()
            ErrorLogger.error(f"APIキー更新エラー: {str(e)}")
            raise
    
    async def delete_api_key(self, api_key_id: str, tenant_id: str) -> bool:
        """
        APIキー削除
        
        引数:
            api_key_id: APIキーID
            tenant_id: テナントID
        戻り値:
            bool: 削除成功時True
        """
        try:
            # APIキー取得
            api_key = await self.get_api_key(api_key_id, tenant_id)
            if not api_key:
                return False
            
            await self.db.delete(api_key)
            await self.db.commit()
            
            SecurityLogger.log_user_action(
                tenant_id,
                "delete_api_key",
                "api_key",
                {"api_key_id": api_key_id, "provider": api_key.provider}
            )
            
            logger.info(f"APIキー削除完了: tenant={tenant_id}, api_key_id={api_key_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            ErrorLogger.error(f"APIキー削除エラー: {str(e)}")
            raise
    
    async def get_active_api_key_by_provider(self, tenant_id: str, provider: str) -> Optional[ApiKey]:
        """
        プロバイダー別のアクティブAPIキー取得
        
        引数:
            tenant_id: テナントID
            provider: プロバイダー名
        戻り値:
            Optional[ApiKey]: アクティブなAPIキー（存在しない場合はNone）
        """
        try:
            query = select(ApiKey).where(
                and_(
                    ApiKey.tenant_id == tenant_id,
                    ApiKey.provider == provider,
                    ApiKey.is_active == True
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            ErrorLogger.error(f"プロバイダー別APIキー取得エラー: {str(e)}")
            raise
    
    def get_decrypted_api_key(self, api_key: ApiKey) -> str:
        """
        復号化されたAPIキーを取得
        
        引数:
            api_key: APIキーオブジェクト
        戻り値:
            str: 復号化されたAPIキー
        """
        return self._decrypt_api_key(api_key.api_key)
