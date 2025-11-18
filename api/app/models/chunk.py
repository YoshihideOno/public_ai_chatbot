"""
チャンクモデル

このファイルはファイルのチャンク（分割されたテキスト片）を管理するためのSQLAlchemyモデルを定義します。
RAGシステムにおけるベクトル検索の基盤となる重要なモデルです。

主な機能:
- チャンク情報の管理
- ベクトル埋め込みの保存
- ファイルとの関連付け
- テナント分離
- メタデータ管理
- インデックス管理
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class Chunk(Base):
    """
    チャンクモデル
    
    ファイルから分割されたテキストチャンクを管理するモデルです。
    RAGシステムにおけるベクトル検索の基盤となる重要なモデルです。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: チャンクの一意識別子（UUID）
        file_id: 所属ファイルID（外部キー）
        tenant_id: 所属テナントID（外部キー）
        chunk_index: チャンクのインデックス番号
        chunk_text: チャンクのテキスト内容
        metadata_json: メタデータ（JSON）
        vector_id: ベクトルデータベースのID
        embedding: ベクトル埋め込み（1536次元）
        created_at: 作成日時
    """
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("file_id", "chunk_index", name="chunks_file_chunk_unique"),
        Index(
            "idx_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    metadata_json = Column('metadata', JSONB, nullable=False, server_default='{}')
    vector_id = Column(String(255), nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    file = relationship("File", back_populates="chunks")
    tenant = relationship("Tenant")
