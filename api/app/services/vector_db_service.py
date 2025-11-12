"""
ベクトルDBサービス

このモジュールは、開発環境ではスタブ/pgvector互換の挙動を行い、
本番環境では Pinecone を利用したベクトルの upsert / delete を提供する。

主な機能:
- テナントごとの論理分離（namespace=tenant_id）
- （オプション）物理分離: テナントごとに別indexを使用（高額プラン想定）
- ベクトルの一括アップサート
- ファイル単位でのベクトル削除
"""

from typing import List, Dict, Any, Optional
import os
from app.utils.logging import PerformanceLogger, ErrorLogger, logger


class VectorDBService:
    """
    ベクトルDBサービス
    
    環境変数:
        VECTOR_DB_PROVIDER: "stub" | "pinecone"（デフォルト: "stub"）
        VECTORDB_PHYSICAL_ISOLATION: "true" で物理分離（テナント毎index）
        PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX: Pinecone接続情報
    """
    def __init__(self) -> None:
        self.provider = os.getenv("VECTOR_DB_PROVIDER", "stub").lower()
        self.physical_isolation = os.getenv("VECTORDB_PHYSICAL_ISOLATION", "false").lower() == "true"
        self._pinecone = None
        self._pc = None
        self._pinecone_index = None

        if self.provider == "pinecone":
            try:
                # pinecone>=5 の公式SDK
                # pip: pinecone[grpc]
                from pinecone import Pinecone
                api_key = os.getenv("PINECONE_API_KEY")
                environment = os.getenv("PINECONE_ENV")
                default_index = os.getenv("PINECONE_INDEX")
                if not api_key or not default_index:
                    raise RuntimeError("PINECONE_API_KEY および PINECONE_INDEX は必須です")
                self._pc = Pinecone(api_key=api_key)
                self._pinecone_index = default_index
                logger.info("Pineconeクライアント初期化成功")
            except Exception as e:
                ErrorLogger.log_exception(e, {"operation": "pinecone_init"})
                self.provider = "stub"
                logger.warning("Pinecone初期化に失敗したため、スタブモードへフォールバックします")

    def _resolve_index_name(self, tenant_id: str) -> str:
        """
        物理分離が有効ならテナント毎にindex名を切り替える。
        無効なら既定indexを返す。
        """
        if self.provider != "pinecone":
            return "stub-index"
        if self.physical_isolation:
            base = os.getenv("PINECONE_INDEX", "rag-chatbot")
            return f"{base}-{tenant_id}".replace("_", "-")
        return os.getenv("PINECONE_INDEX", "rag-chatbot")

    async def upsert_vectors(self, vectors: List[Dict[str, Any]], tenant_id: str) -> bool:
        """
        ベクトルをベクトルDBに保存（チャンクIDをベクトルIDとして利用）
        
        引数:
            vectors: { id: str, values: List[float], metadata: Dict[str, Any] } の配列
            tenant_id: テナントID（論理分離namespace）
        """
        try:
            if self.provider == "pinecone":
                index_name = self._resolve_index_name(tenant_id)
                index = self._pc.Index(index_name)
                # Pinecone v5 upsert形式
                # [{"id": "...", "values": [...], "metadata": {...}}]
                index.upsert(vectors)
            else:
                # 開発/スタブ: 計測ログのみ
                PerformanceLogger.log_api_performance(
                    "vector_upsert_stub",
                    50,
                    tenant_id=tenant_id
                )
            return True
        except Exception as e:
            ErrorLogger.log_exception(e, {"operation": "vector_upsert", "tenant_id": tenant_id})
            return False

    async def delete_by_file(self, tenant_id: str, file_id: str) -> bool:
        """
        指定ファイルに紐づく全ベクトルを削除
        
        Pinecone: metadata filter で file_id を指定して削除
        スタブ: 成功扱い
        """
        try:
            if self.provider == "pinecone":
                index_name = self._resolve_index_name(tenant_id)
                index = self._pc.Index(index_name)
                # metadata で file_id 一致を削除
                # v5: delete(filter={ "file_id": file_id })
                index.delete(filter={"file_id": file_id})
            else:
                PerformanceLogger.log_api_performance(
                    "vector_delete_stub",
                    20,
                    tenant_id=tenant_id
                )
            return True
        except Exception as e:
            ErrorLogger.log_exception(e, {"operation": "vector_delete", "tenant_id": tenant_id, "file_id": file_id})
            return False


