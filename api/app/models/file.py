"""
ファイル管理モデル

このファイルはファイル（コンテンツ）情報を管理するためのSQLAlchemyモデルを定義します。
ファイルのアップロード、処理状態、メタデータ管理などの機能を提供します。

主な機能:
- ファイル基本情報の管理
- ファイルタイプ・ステータス管理
- テナントとの関連付け
- チャンクとの関連付け
- メタデータ管理
- 処理状態の追跡
"""

from sqlalchemy import Column, String, DateTime, Text, BigInteger, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class FileType(str, enum.Enum):
    """
    ファイルタイプ列挙型
    
    システムでサポートするファイル形式を定義します。
    各タイプに応じた処理方法を決定するために使用されます。
    
    値:
        PDF: PDFファイル
        HTML: HTMLファイル
        MD: Markdownファイル
        CSV: CSVファイル
        TXT: テキストファイル
    """
    PDF = "PDF"
    HTML = "HTML"
    MD = "MD"
    CSV = "CSV"
    TXT = "TXT"


class FileStatus(str, enum.Enum):
    """
    ファイルステータス列挙型
    
    ファイルの処理状態を定義します。
    アップロードからインデックス化までの処理フローを管理します。
    
    値:
        UPLOADED: アップロード完了
        PROCESSING: 処理中
        INDEXED: インデックス化完了
        FAILED: 処理失敗
    """
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class File(Base):
    """
    ファイルモデル
    
    アップロードされたファイルの情報を管理するモデルです。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: ファイルの一意識別子（UUID）
        tenant_id: 所属テナントID（外部キー）
        title: ファイルタイトル
        file_name: ファイル名
        file_type: ファイルタイプ
        size_bytes: ファイルサイズ（バイト）
        status: 処理ステータス
        s3_key: S3ストレージのキー
        uploaded_by: アップロード者ID（外部キー）
        description: ファイルの説明
        tags: タグ情報（JSON配列）
        metadata_json: メタデータ（JSON）
        uploaded_at: アップロード日時
        indexed_at: インデックス化日時
        chunk_count: チャンク数
        error_message: エラーメッセージ
        created_at: 作成日時
        updated_at: 更新日時
        deleted_at: 削除日時（ソフトデリート用）
    """
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    status = Column(Enum(FileStatus), nullable=False, default=FileStatus.UPLOADED)
    s3_key = Column(String(1000), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=False, server_default='[]')
    metadata_json = Column('metadata', JSONB, nullable=False, server_default='{}')
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    chunk_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="files")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")
