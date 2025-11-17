from sqlalchemy import Column, String, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    model = Column(String(100), nullable=False)
    tokens_in = Column(Integer, nullable=False, default=0)
    tokens_out = Column(Integer, nullable=False, default=0)
    cost = Column(Numeric(10, 4), nullable=False, default=0)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
