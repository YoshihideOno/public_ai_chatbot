from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(String(255), nullable=False)
    user_input = Column(Text, nullable=False)
    bot_output = Column(Text, nullable=False)
    referenced_chunks = Column(JSONB, nullable=False, server_default='[]')
    model = Column(String(100), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    feedback = Column(String(50), nullable=True)
    feedback_comment = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
