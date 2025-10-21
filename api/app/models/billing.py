from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class BillingInfo(Base):
    __tablename__ = "billing_info"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    
    # Stripe
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    stripe_payment_method_id = Column(String(255), nullable=True)
    
    # Plan / Status
    plan = Column(String(50), nullable=False, default='FREE')  # FREE/BASIC/PRO/ENTERPRISE
    status = Column(String(50), nullable=False, default='ACTIVE')  # ACTIVE/PAST_DUE/CANCELED/TRIALING
    billing_cycle = Column(String(50), nullable=False, default='MONTHLY')  # MONTHLY/YEARLY
    
    # Billing contact
    billing_email = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    billing_address = Column(JSONB, nullable=False, server_default='{}')
    tax_id = Column(String(100), nullable=True)
    
    # Period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Quotas / Usage
    quota_queries = Column(Integer, nullable=False, server_default='100')
    quota_storage_mb = Column(Integer, nullable=False, server_default='100')
    usage_queries = Column(Integer, nullable=False, server_default='0')
    usage_storage_mb = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True)
    billing_info_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Stripe
    stripe_invoice_id = Column(String(255), nullable=True, unique=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    # Invoice
    invoice_number = Column(String(100), nullable=False, unique=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False, server_default='0')
    total = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='JPY')
    status = Column(String(50), nullable=False, default='DRAFT')  # DRAFT/OPEN/PAID/VOID/UNCOLLECTIBLE
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    pdf_url = Column(String(1000), nullable=True)
    line_items = Column(JSONB, nullable=False, server_default='[]')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
