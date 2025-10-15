from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class IndexingJob(Base):
    __tablename__ = "indexing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="QUEUED")
    started_at = Column(DateTime(timezone=False), nullable=True)
    completed_at = Column(DateTime(timezone=False), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.current_timestamp())
