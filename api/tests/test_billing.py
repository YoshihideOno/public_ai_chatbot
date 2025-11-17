"""
課金APIテストファイル

このファイルは課金関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、Stripeモック使用を含みます。
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.config import settings
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


@pytest.mark.asyncio
@patch('app.api.v1.endpoints.billing.stripe.checkout.Session.create')
@patch('app.services.billing_service.BillingService.get_or_create_billing_info', new_callable=AsyncMock)
@patch('app.core.config.settings.STRIPE_PRICE_BASIC_MONTHLY', "price_test_basic_monthly")
@patch('app.core.config.settings.STRIPE_SECRET_KEY', "sk_test_key")
@patch('app.core.config.settings.APP_URL', "http://localhost:3000")
async def test_create_checkout_session_success(mock_billing_info: MagicMock, mock_stripe_create: MagicMock, client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: Checkout Session作成
    """
    # Stripeモックの設定
    mock_session = MagicMock()
    mock_session.id = "cs_test_1234567890"
    mock_session.url = "https://checkout.stripe.com/test"
    mock_stripe_create.return_value = mock_session
    
    # AsyncMockの戻り値を設定
    mock_billing_info.return_value = MagicMock()
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"billing-{unique_id}@example.com"
    password = "BillingPassword1"
    tenant_name = f"Billing Tenant {unique_id}"
    tenant_domain = f"billing-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # Checkout Session作成
        response = client.post(
            f"{settings.API_V1_STR}/billing/checkout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "plan": "BASIC",
                "billing_cycle": "MONTHLY"
            }
        )
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "url" in data
        mock_stripe_create.assert_called_once()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
@patch('app.api.v1.endpoints.billing.stripe.checkout.Session.create')
@patch('app.services.billing_service.BillingService.get_or_create_billing_info', new_callable=AsyncMock)
@patch('app.core.config.settings.STRIPE_PRICE_PRO_YEARLY', "price_test_pro_yearly")
@patch('app.core.config.settings.STRIPE_SECRET_KEY', "sk_test_key")
@patch('app.core.config.settings.APP_URL', "http://localhost:3000")
async def test_create_checkout_session_yearly(mock_billing_info: MagicMock, mock_stripe_create: MagicMock, client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 年次プランでCheckout Session作成
    """
    # Stripeモックの設定
    mock_session = MagicMock()
    mock_session.id = "cs_test_1234567890"
    mock_session.url = "https://checkout.stripe.com/test"
    mock_stripe_create.return_value = mock_session
    
    # AsyncMockの戻り値を設定
    mock_billing_info.return_value = MagicMock()
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"billing-yearly-{unique_id}@example.com"
    password = "BillingYearlyPassword1"
    tenant_name = f"Billing Yearly Tenant {unique_id}"
    tenant_domain = f"billing-yearly-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 年次プランでCheckout Session作成
        response = client.post(
            f"{settings.API_V1_STR}/billing/checkout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "plan": "PRO",
                "billing_cycle": "YEARLY"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "url" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_create_checkout_session_invalid_plan(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 無効なプランでCheckout Session作成
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"billing-invalid-{unique_id}@example.com"
    password = "BillingInvalidPassword1"
    tenant_name = f"Billing Invalid Tenant {unique_id}"
    tenant_domain = f"billing-invalid-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 無効なプランでCheckout Session作成
        response = client.post(
            f"{settings.API_V1_STR}/billing/checkout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "plan": "INVALID_PLAN",
                "billing_cycle": "MONTHLY"
            }
        )
        assert response.status_code == 422
        assert "無効なプラン" in response.json()["detail"] or "invalid" in response.json()["detail"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
@patch('app.api.v1.endpoints.billing.stripe.checkout.Session.create')
@patch('app.services.billing_service.BillingService.get_or_create_billing_info', new_callable=AsyncMock)
@patch('app.core.config.settings.STRIPE_PRICE_BASIC_MONTHLY', "price_test_basic_monthly")
@patch('app.core.config.settings.STRIPE_SECRET_KEY', "sk_test_key")
@patch('app.core.config.settings.APP_URL', "http://localhost:3000")
async def test_create_checkout_session_stripe_error(mock_billing_info: AsyncMock, mock_stripe_create: MagicMock, client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: Stripe APIエラー
    """
    # Stripeエラーをモック
    import stripe
    mock_stripe_create.side_effect = stripe.error.StripeError("Stripe API error")
    mock_billing_info.return_value = MagicMock()
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"billing-error-{unique_id}@example.com"
    password = "BillingErrorPassword1"
    tenant_name = f"Billing Error Tenant {unique_id}"
    tenant_domain = f"billing-error-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # Checkout Session作成（Stripeエラー）
        response = client.post(
            f"{settings.API_V1_STR}/billing/checkout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "plan": "BASIC",
                "billing_cycle": "MONTHLY"
            }
        )
        assert response.status_code == 500
        assert "失敗" in response.json()["detail"] or "failed" in response.json()["detail"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
@patch('stripe.Webhook.construct_event')
@patch('app.core.config.settings.STRIPE_WEBHOOK_SECRET', "test_webhook_secret")
@patch('app.core.config.settings.STRIPE_SECRET_KEY', "test_secret_key")
async def test_stripe_webhook_success(mock_construct_event: MagicMock, client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: Stripe Webhook受信
    """
    # Webhookイベントをモック
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_1234567890",
                "metadata": {
                    "tenant_id": str(uuid.uuid4()),
                    "plan": "BASIC",
                    "billing_cycle": "MONTHLY"
                }
            }
        }
    }
    mock_construct_event.return_value = mock_event
    
    # Webhookリクエスト
    response = client.post(
        f"{settings.API_V1_STR}/billing/webhooks/stripe",
        headers={
            "stripe-signature": "test_signature"
        },
        content=b"test_payload"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["received"] == True


@pytest.mark.asyncio
@patch('stripe.Webhook.construct_event')
@patch('app.core.config.settings.STRIPE_WEBHOOK_SECRET', "test_webhook_secret")
@patch('app.core.config.settings.STRIPE_SECRET_KEY', "test_secret_key")
async def test_stripe_webhook_signature_verification_error(mock_construct_event: MagicMock, client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: Stripe署名検証失敗
    """
    import stripe
    # 署名検証エラーをモック
    mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
        "Invalid signature",
        "test_signature"
    )
    
    # Webhookリクエスト（無効な署名）
    response = client.post(
        f"{settings.API_V1_STR}/billing/webhooks/stripe",
        headers={
            "stripe-signature": "invalid_signature"
        },
        content=b"test_payload"
    )
    assert response.status_code == 400
    assert "署名検証" in response.json()["detail"] or "signature" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_checkout_session_no_auth(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 認証トークンなしでCheckout Session作成
    """
    response = client.post(
        f"{settings.API_V1_STR}/billing/checkout",
        json={
            "plan": "BASIC",
            "billing_cycle": "MONTHLY"
        }
    )
    assert response.status_code in [401, 403]  # FastAPIのHTTPBearerは認証トークンがない場合403を返す可能性がある


@pytest.mark.asyncio
async def test_create_checkout_session_no_tenant(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: テナント未設定でCheckout Session作成
    """
    from tests.test_auth import register_user, cleanup_user
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"notenant-billing-{unique_id}@example.com"
    password = "NoTenantBillingPassword1"
    username = f"nobill{unique_id}"
    
    try:
        register_user(client, email, password, username)
        _, access_token = get_authenticated_client(client, email, password)
        
        # Checkout Session作成を試行（テナント未設定のためエラー）
        response = client.post(
            f"{settings.API_V1_STR}/billing/checkout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "plan": "BASIC",
                "billing_cycle": "MONTHLY"
            }
        )
        # テナント未設定の場合はエラーになる可能性がある
        assert response.status_code in [400, 403, 500]
    finally:
        await cleanup_user(db_session, email)

