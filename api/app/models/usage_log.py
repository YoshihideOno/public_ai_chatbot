from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"
    __table_args__ = (
        Index("ix_usage_logs_tenant_id", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    model = Column(String(100), nullable=False)
    tokens_in = Column(Integer, nullable=False, default=0)
    tokens_out = Column(Integer, nullable=False, default=0)
    cost = Column(Numeric(10, 4), nullable=False, default=0)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
