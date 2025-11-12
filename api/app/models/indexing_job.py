"""
インデックス化ジョブモデル

このファイルはファイルのインデックス化処理の状態を管理するためのSQLAlchemyモデルを定義します。
将来のジョブキューシステムや再試行機能、進捗管理のために用意されています。

主な機能:
- インデックス化ジョブの状態管理
- 進捗状況の記録
- 再試行回数の管理
- エラーメッセージの保存
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class IndexingJob(Base):
    """
    インデックス化ジョブモデル
    
    ファイルのインデックス化処理の状態を管理するモデルです。
    将来のジョブキューシステムや再試行機能、進捗管理のために用意されています。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: ジョブの一意識別子（UUID）
        tenant_id: 所属テナントID（外部キー）
        file_id: 処理対象ファイルID（外部キー）
        status: ジョブステータス（QUEUED, PROCESSING, COMPLETED, FAILED等）
        progress: 処理進捗（0-100の整数）
        started_at: 処理開始日時
        completed_at: 処理完了日時
        error_message: エラーメッセージ
        retry_count: 再試行回数
        created_at: 作成日時
        updated_at: 更新日時
    """
    __tablename__ = "indexing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="QUEUED")
    progress = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 進捗の範囲チェック制約（0-100）
    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
    )
