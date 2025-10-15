"""
課金・決済APIエンドポイント

Stripe Checkout開始とWebhook受信を処理します。
認証・認可、バリデーション、エラーハンドリングは統一方針に従います。
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal
from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.schemas.user import User
from app.services.billing_service import BillingService
from app.utils.logging import BusinessLogger, ErrorLogger
import stripe

router = APIRouter()


@router.post("/checkout")
async def create_checkout_session(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Checkout Sessionを作成
    
    引数:
        payload: { plan: 'BASIC'|'PRO', billing_cycle: 'MONTHLY'|'YEARLY' }
        db: DBセッション
        current_user: 認証済みユーザー
    戻り値:
        { url: str, session_id: str }
    """
    plan: Literal['BASIC', 'PRO'] = payload.get("plan")
    billing_cycle: Literal['MONTHLY', 'YEARLY'] = payload.get("billing_cycle", "MONTHLY")
    if plan not in ("BASIC", "PRO"):
        raise HTTPException(status_code=422, detail="無効なプランです")

    price_map = {
        ("BASIC", "MONTHLY"): settings.STRIPE_PRICE_BASIC_MONTHLY,
        ("BASIC", "YEARLY"): settings.STRIPE_PRICE_BASIC_YEARLY,
        ("PRO", "MONTHLY"): settings.STRIPE_PRICE_PRO_MONTHLY,
        ("PRO", "YEARLY"): settings.STRIPE_PRICE_PRO_YEARLY,
    }
    price_id = price_map.get((plan, billing_cycle))
    if not price_id:
        raise HTTPException(status_code=500, detail="価格IDが設定されていません")

    billing = BillingService(db)
    await billing.get_or_create_billing_info(str(current_user.tenant_id), current_user.email)

    # Stripe SDKでCheckout Session作成
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe未設定")
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # 成功URL/キャンセルURL
    success_url = f"{settings.APP_URL}/billing/success"
    cancel_url = f"{settings.APP_URL}/billing/plans"
    try:
        session = stripe.checkout.sessions.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "tenant_id": str(current_user.tenant_id),
                "plan": plan,
                "billing_cycle": billing_cycle,
            },
        )
        BusinessLogger.info(
            f"Checkoutセッション作成: tenant={current_user.tenant_id}, plan={plan}, cycle={billing_cycle}"
        )
        return {"session_id": session.id, "url": session.url}
    except Exception as e:
        ErrorLogger.error(f"Stripeセッション作成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="Checkoutの作成に失敗しました")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Stripe Webhook受信
    
    署名検証後、イベントタイプに応じて課金情報を更新します。
    ここではスケルトン実装として200 OKのみ返します。
    """
    try:
        if not settings.STRIPE_WEBHOOK_SECRET or not settings.STRIPE_SECRET_KEY:
            raise HTTPException(status_code=500, detail="Stripe未設定")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        payload = await request.body()
        sig = request.headers.get("stripe-signature")
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig, secret=settings.STRIPE_WEBHOOK_SECRET
        )

        event_type = event["type"]
        BusinessLogger.info(f"Stripe Webhook受信: {event_type}")
        # ここでBillingServiceを呼び出して各イベントを反映（省略）
        return {"received": True}
    except stripe.error.SignatureVerificationError as e:
        ErrorLogger.error(f"Stripe署名検証失敗: {str(e)}")
        raise HTTPException(status_code=400, detail="署名検証に失敗しました")
    except Exception as e:
        ErrorLogger.error(f"Stripe Webhook処理エラー: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook処理に失敗しました")


