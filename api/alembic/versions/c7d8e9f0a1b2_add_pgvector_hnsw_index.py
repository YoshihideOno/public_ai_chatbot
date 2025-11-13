"""add pgvector hnsw index

chunksテーブルのembeddingカラムにHNSWインデックスを追加して、
ベクトル検索のパフォーマンスを向上させます。

Revision ID: c7d8e9f0a1b2
Revises: 79c3d1e5b6ef
Create Date: 2025-11-13 00:44:51.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = '79c3d1e5b6ef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    chunksテーブルのembeddingカラムにHNSWインデックスを追加
    
    HNSW (Hierarchical Navigable Small World) インデックスは、
    pgvectorで高速なベクトル類似度検索を実現するためのインデックスです。
    
    パラメータ:
    - m: 各ノードが接続する最大のエッジ数（デフォルト: 16）
    - ef_construction: インデックス構築時の探索範囲（デフォルト: 64）
    
    これらの値は、インデックスサイズと検索速度のバランスを取ります。
    より大きな値は検索速度を向上させますが、インデックスサイズも増加します。
    """
    # pgvector拡張が有効であることを確認
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # HNSWインデックスを作成（L2距離用）
    # vector_l2_opsはL2距離（ユークリッド距離）検索用のオペレータクラス
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
        ON chunks 
        USING hnsw (embedding vector_l2_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    """
    HNSWインデックスを削除
    """
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw")

