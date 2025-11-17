"""
課金管理サービス

このファイルはStripeを用いたサブスクリプション課金のビジネスロジックを実装します。
Checkoutセッション作成、Webhookイベント処理、課金情報の更新を担当します。

主な機能:
- Checkout Sessionの作成
- 顧客情報の取得/作成
- Webhookイベント処理（checkout.session.completed等）
- billing_info/invoicesの更新
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import uuid
from app.core.config import settings
from app.utils.logging import BusinessLogger, ErrorLogger, logger
from app.models.billing import BillingInfo, Invoice
from sqlalchemy import select


class BillingService:
    """
    課金管理サービス
    
    Stripe連携によるサブスクリプション課金処理を行います。
    データベース更新と外部サービス通信の橋渡しを行います。
    
    属性:
        db: データベースセッション（AsyncSession）
    """
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        引数:
            db: データベースセッション
        """
        self.db = db

    async def get_or_create_billing_info(self, tenant_id: str, billing_email: Optional[str] = None) -> BillingInfo:
        """
        テナントの課金情報を取得、存在しない場合は作成
        
        引数:
            tenant_id: テナントID
            billing_email: 請求メール（新規作成時に使用）
        戻り値:
            BillingInfo: 課金情報
        """
        from uuid import UUID as UUIDType
        tenant_uuid = UUIDType(tenant_id) if isinstance(tenant_id, str) else tenant_id
        result = await self.db.execute(select(BillingInfo).where(BillingInfo.tenant_id == tenant_uuid))
        info = result.scalar_one_or_none()
        if info:
            return info
        info = BillingInfo(id=uuid.uuid4(), tenant_id=tenant_uuid, billing_email=billing_email or "")
        self.db.add(info)
        await self.db.commit()
        await self.db.refresh(info)
        logger.info(f"BillingInfo作成: tenant={tenant_id}")
        return info

    async def update_subscription_status(self, tenant_id: str, data: Dict[str, Any]) -> None:
        """
        サブスクリプションステータス更新
        
        引数:
            tenant_id: テナントID
            data: 更新データ（stripe IDsや期間、プランなど）
        戻り値:
            なし
        """
        result = await self.db.execute(select(BillingInfo).where(BillingInfo.tenant_id == tenant_id))
        info = result.scalar_one_or_none()
        if not info:
            raise ValueError("billing_infoが存在しません")
        for k, v in data.items():
            setattr(info, k, v)
        await self.db.commit()
        logger.info(f"課金情報更新: tenant={tenant_id}, fields={list(data.keys())}")


