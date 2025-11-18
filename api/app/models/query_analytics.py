"""
クエリアナリティクス（自動集計FAQ用）モデル

このファイルは会話ログから自動集計されたクエリのクラスタおよび
トップクエリ集計結果を管理するSQLAlchemyモデルを定義します。
テナント分離・多言語・期間別の管理を前提とします。

主な機能:
- クラスタ情報（LLM命名、確信度、代表サンプル）の保存
- 期間別トップクエリ集計（回数、評価率、平均応答時間、クラスタ紐付け）の保存
"""

from sqlalchemy import Column, String, DateTime, Integer, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class QueryCluster(Base):
    """
    クエリクラスタモデル

    会話ログから抽出したクエリをクラスタリングし、
    LLMで命名したラベルや確信度、代表サンプルを保持します。
    Baseを継承し、テナント分離・期間・言語でスコープします。

    属性:
        id: 一意識別子（UUID）
        tenant_id: テナントID（UUID）
        locale: 言語コード（例: ja, en）
        period_start: 期間開始（含む）
        period_end: 期間終了（含む）
        cluster_id: 期間内のクラスタID（整数、論理的一意）
        label: LLMが命名したクラスタ名
        confidence: ラベルの確信度（0.00-1.00）
        sample_queries: 代表サンプル（最大5件程度）
        created_at/updated_at: 監査用タイムスタンプ
    """
    __tablename__ = "query_clusters"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "locale", "period_start", "period_end", "cluster_id",
            name="uq_query_clusters_scope_cluster"
        ),
        Index("ix_query_clusters_tenant", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    locale = Column(String(10), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    cluster_id = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)
    sample_queries = Column(JSONB, nullable=False, server_default='[]')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class TopQueryAggregate(Base):
    """
    トップクエリ集計モデル

    期間内の上位クエリをランキングとして保持します。
    クエリ文、回数、評価率、平均応答時間、対応クラスタIDを保持します。

    属性:
        id: 一意識別子（UUID）
        tenant_id: テナントID
        locale: 言語コード
        period_start/period_end: 期間
        rank: ランキング順位（1起点）
        query: 代表クエリ文
        count: 出現回数
        like_rate: いいね率（0-1）
        avg_response_time_ms: 平均応答時間（ミリ秒）
        cluster_id: 紐付くクラスタID（論理外部キー）
    """
    __tablename__ = "top_query_aggregates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "locale", "period_start", "period_end", "rank",
            name="uq_top_query_aggregates_scope_rank"
        ),
        Index("ix_top_query_aggregates_tenant", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    locale = Column(String(10), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    query = Column(String, nullable=False)
    count = Column(Integer, nullable=False)
    like_rate = Column(Numeric(4, 3), nullable=False)
    avg_response_time_ms = Column(Numeric, nullable=False)
    cluster_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


