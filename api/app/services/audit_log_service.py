"""
監査ログサービス

このファイルは監査ログに関するビジネスロジックを実装します。
システム操作の監査記録をデータベースに保存する機能を提供します。

主な機能:
- 監査ログの作成
- IPアドレスとUser-Agentの取得
- テナント分離
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from uuid import UUID
import uuid
from fastapi import Request

from app.models.audit_log import AuditLog
from app.utils.logging import logger
from app.utils.common import DateTimeUtils


class AuditLogService:
    """
    監査ログサービス
    
    監査ログに関する全てのビジネスロジックを担当します。
    システム操作の監査記録をデータベースに保存します。
    
    属性:
        db: データベースセッション（AsyncSession）
    """
    
    def __init__(self, db: AsyncSession):
        """
        監査ログサービスの初期化
        
        引数:
            db: データベースセッション
        """
        self.db = db
    
    @staticmethod
    def get_client_ip(request: Optional[Request] = None) -> str:
        """
        クライアントIPアドレスを取得
        
        リクエストヘッダーから実際のクライアントIPを取得します。
        プロキシ経由の場合はX-Forwarded-Forヘッダーを確認します。
        
        引数:
            request: FastAPIのRequestオブジェクト
        
        戻り値:
            str: IPアドレス（取得できない場合は"0.0.0.0"）
        """
        if not request:
            return "0.0.0.0"
        
        # X-Forwarded-Forヘッダーを確認（プロキシ経由の場合）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # カンマ区切りの場合は最初のIPを使用
            ip = forwarded_for.split(",")[0].strip()
            if ip:
                return ip
        
        # X-Real-IPヘッダーを確認
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 直接接続の場合
        if request.client:
            return request.client.host
        
        return "0.0.0.0"
    
    @staticmethod
    def get_user_agent(request: Optional[Request] = None) -> Optional[str]:
        """
        User-Agentを取得
        
        引数:
            request: FastAPIのRequestオブジェクト
        
        戻り値:
            Optional[str]: User-Agent文字列（取得できない場合はNone）
        """
        if not request:
            return None
        
        return request.headers.get("User-Agent")
    
    async def create_audit_log(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        監査ログを作成
        
        システム操作の監査記録をデータベースに保存します。
        
        引数:
            tenant_id: テナントID（必須）
            action: アクション名（例: "login", "create_user"）
            resource_type: リソースタイプ（例: "user", "content", "tenant"）
            user_id: ユーザーID（オプション）
            resource_id: リソースID（オプション）
            request: FastAPIのRequestオブジェクト（IPアドレスとUser-Agent取得用）
            details: 追加の詳細情報（JSON形式）
        
        戻り値:
            AuditLog: 作成された監査ログオブジェクト
        
        例外:
            Exception: データベース操作エラー
        """
        try:
            # IPアドレスとUser-Agentを取得
            ip_address = self.get_client_ip(request)
            user_agent = self.get_user_agent(request)
            
            # UUIDに変換
            tenant_uuid = UUID(tenant_id) if tenant_id else None
            user_uuid = UUID(user_id) if user_id else None
            resource_uuid = UUID(resource_id) if resource_id else None
            
            # 監査ログオブジェクトを作成
            audit_log = AuditLog(
                id=uuid.uuid4(),
                tenant_id=tenant_uuid,
                user_id=user_uuid,
                action=action,
                resource_type=resource_type,
                resource_id=resource_uuid,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {}
            )
            
            # データベースに保存
            self.db.add(audit_log)
            await self.db.commit()
            await self.db.refresh(audit_log)
            
            logger.debug(
                f"監査ログを作成: action={action}, resource_type={resource_type}, "
                f"tenant_id={tenant_id}, user_id={user_id}"
            )
            
            return audit_log
            
        except Exception as e:
            # エラーが発生してもログに記録するが、メイン処理は継続
            logger.error(
                f"監査ログの作成に失敗: action={action}, resource_type={resource_type}, "
                f"tenant_id={tenant_id}, error={str(e)}",
                exc_info=True
            )
            await self.db.rollback()
            # エラーを再発生させない（メイン処理への影響を最小化）
            raise

