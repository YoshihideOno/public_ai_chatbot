"""
コンテンツ管理サービス

このファイルはコンテンツ（ファイル）に関するビジネスロジックを実装します。
ファイルのアップロード、処理、検索、チャンク管理などの機能を提供します。

主な機能:
- コンテンツのCRUD操作
- ファイルアップロード・処理
- チャンク分割・管理
- ベクトル検索
- メタデータ管理
- テナント分離
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import base64
from app.models.file import File, FileType, FileStatus
from app.models.chunk import Chunk
from app.schemas.content import (
    ContentCreate, ContentUpdate, ContentSearchParams,
    ContentSearchResult, ChunkCreate, ChunkUpdate
)
from app.utils.common import StringUtils, ValidationUtils, FileUtils
from app.utils.logging import BusinessLogger, ErrorLogger


class ContentService:
    """
    コンテンツ管理サービス
    
    コンテンツ（ファイル）に関する全てのビジネスロジックを担当します。
    ファイルのアップロード、処理、検索、チャンク管理などを統合的に管理します。
    
    属性:
        db: データベースセッション（AsyncSession）
    """
    def __init__(self, db: AsyncSession):
        """
        コンテンツサービスの初期化
        
        引数:
            db: データベースセッション
            
        戻り値:
            ContentService: コンテンツサービスインスタンス
        """
        self.db = db

    async def get_by_id(self, content_id: str, tenant_id: str) -> Optional[File]:
        """
        コンテンツIDでコンテンツ情報を取得
        
        引数:
            content_id: コンテンツの一意識別子
            tenant_id: テナントID（テナント分離用）
            
        戻り値:
            File: コンテンツ情報、存在しない場合はNone
            
        例外:
            SQLAlchemyError: データベースエラー
        """
        try:
            if not content_id or not tenant_id:
                BusinessLogger.warning(f"無効なパラメータ: content_id={content_id}, tenant_id={tenant_id}")
                return None
                
            result = await self.db.execute(
                select(File)
                .options(selectinload(File.chunks))
                .where(
                    and_(
                        File.id == content_id,
                        File.tenant_id == tenant_id,
                        File.deleted_at.is_(None)
                    )
                )
            )
            content = result.scalar_one_or_none()
            
            if content:
                BusinessLogger.info(f"コンテンツ取得成功: ID {content_id}")
            else:
                BusinessLogger.info(f"コンテンツ未発見: ID {content_id}")
                
            return content
        except Exception as e:
            BusinessLogger.error(f"コンテンツ取得エラー: {str(e)}")
            raise
        return result.scalar_one_or_none()

    async def get_all_contents(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        file_type: Optional[FileType] = None,
        status: Optional[FileStatus] = None,
        search_query: Optional[str] = None
    ) -> List[File]:
        """コンテンツ一覧取得（ページネーション対応）"""
        query = select(File).where(
            and_(
                File.tenant_id == tenant_id,
                File.deleted_at.is_(None)
            )
        )
        
        if file_type:
            query = query.where(File.file_type == file_type)
        
        if status:
            query = query.where(File.status == status)
        
        if search_query:
            query = query.where(
                or_(
                    File.title.ilike(f"%{search_query}%"),
                    File.description.ilike(f"%{search_query}%")
                )
            )
        
        query = query.order_by(File.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_content(self, content_data: ContentCreate, tenant_id: str, user_id: str) -> File:
        """コンテンツ作成"""
        # ファイルサイズチェック
        if content_data.file_content:
            file_size = len(base64.b64decode(content_data.file_content))
            if not ValidationUtils.validate_file_size(file_size):
                raise ValueError("ファイルサイズが制限を超えています")
        
        # S3キー生成（仮実装）
        s3_key = f"tenant/{tenant_id}/files/{uuid.uuid4()}"
        
        # ファイル作成
        db_file = File(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=content_data.title,
            file_name=f"{content_data.title}.{content_data.content_type.value.lower()}",
            file_type=content_data.content_type,
            size_bytes=len(base64.b64decode(content_data.file_content)) if content_data.file_content else 0,
            s3_key=s3_key,
            uploaded_by=user_id,
            description=content_data.description,
            tags=content_data.tags,
            metadata_json=content_data.metadata
        )
        
        self.db.add(db_file)
        await self.db.commit()
        await self.db.refresh(db_file)
        
        BusinessLogger.log_content_action(
            str(db_file.id),
            "content_created",
            user_id,
            tenant_id
        )
        
        return db_file

    async def update_content(
        self, 
        content_id: str, 
        content_update: ContentUpdate, 
        tenant_id: str
    ) -> Optional[File]:
        """コンテンツ更新"""
        content = await self.get_by_id(content_id, tenant_id)
        if not content:
            return None
        
        update_data = content_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(content, field, value)
        
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        BusinessLogger.log_content_action(
            content_id,
            "content_updated",
            str(content.uploaded_by),
            tenant_id
        )
        
        return content

    async def delete_content(self, content_id: str, tenant_id: str) -> bool:
        """コンテンツ削除（ソフトデリート）"""
        content = await self.get_by_id(content_id, tenant_id)
        if not content:
            return False
        
        content.deleted_at = datetime.utcnow()
        
        await self.db.commit()
        
        BusinessLogger.log_content_action(
            content_id,
            "content_deleted",
            str(content.uploaded_by),
            tenant_id
        )
        
        return True

    async def get_content_chunks(
        self, 
        content_id: str, 
        tenant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chunk]:
        """コンテンツのチャンク一覧取得"""
        result = await self.db.execute(
            select(Chunk)
            .where(
                and_(
                    Chunk.file_id == content_id,
                    Chunk.tenant_id == tenant_id
                )
            )
            .order_by(Chunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_chunk(self, chunk_data: ChunkCreate, tenant_id: str) -> Chunk:
        """チャンク作成"""
        # ファイルの存在確認
        file_result = await self.db.execute(
            select(File).where(
                and_(
                    File.id == chunk_data.file_id,
                    File.tenant_id == tenant_id
                )
            )
        )
        file = file_result.scalar_one_or_none()
        if not file:
            raise ValueError("ファイルが見つかりません")
        
        # チャンク作成
        db_chunk = Chunk(
            id=str(uuid.uuid4()),
            file_id=chunk_data.file_id,
            tenant_id=tenant_id,
            chunk_index=chunk_data.chunk_index,
            chunk_text=chunk_data.content,
            metadata_json=chunk_data.metadata
        )
        
        self.db.add(db_chunk)
        await self.db.commit()
        await self.db.refresh(db_chunk)
        
        return db_chunk

    async def update_chunk(
        self, 
        chunk_id: str, 
        chunk_update: ChunkUpdate, 
        tenant_id: str
    ) -> Optional[Chunk]:
        """チャンク更新"""
        result = await self.db.execute(
            select(Chunk).where(
                and_(
                    Chunk.id == chunk_id,
                    Chunk.tenant_id == tenant_id
                )
            )
        )
        chunk = result.scalar_one_or_none()
        if not chunk:
            return None
        
        update_data = chunk_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(chunk, field, value)
        
        await self.db.commit()
        await self.db.refresh(chunk)
        
        return chunk

    async def delete_chunk(self, chunk_id: str, tenant_id: str) -> bool:
        """チャンク削除"""
        result = await self.db.execute(
            select(Chunk).where(
                and_(
                    Chunk.id == chunk_id,
                    Chunk.tenant_id == tenant_id
                )
            )
        )
        chunk = result.scalar_one_or_none()
        if not chunk:
            return False
        
        await self.db.delete(chunk)
        await self.db.commit()
        
        return True

    async def search_contents(
        self, 
        search_params: ContentSearchParams, 
        tenant_id: str
    ) -> List[ContentSearchResult]:
        """コンテンツ検索"""
        query = select(File).where(
            and_(
                File.tenant_id == tenant_id,
                File.deleted_at.is_(None)
            )
        )
        
        # ファイルタイプフィルタ
        if search_params.file_types:
            query = query.where(File.file_type.in_(search_params.file_types))
        
        # タグフィルタ
        if search_params.tags:
            for tag in search_params.tags:
                query = query.where(File.tags.contains([tag]))
        
        # 日付フィルタ
        if search_params.date_from:
            query = query.where(File.created_at >= search_params.date_from)
        
        if search_params.date_to:
            query = query.where(File.created_at <= search_params.date_to)
        
        # テキスト検索
        if search_params.query:
            query = query.where(
                or_(
                    File.title.ilike(f"%{search_params.query}%"),
                    File.description.ilike(f"%{search_params.query}%")
                )
            )
        
        query = query.order_by(File.created_at.desc())
        query = query.offset(search_params.offset).limit(search_params.limit)
        
        result = await self.db.execute(query)
        files = result.scalars().all()
        
        # 検索結果をContentSearchResultに変換
        search_results = []
        for file in files:
            # 簡易的な関連度スコア計算（実際はベクトル検索を使用）
            relevance_score = 0.8  # 仮の値
            
            # スニペット生成（簡易版）
            snippet = file.description[:200] + "..." if file.description and len(file.description) > 200 else file.description or ""
            
            search_result = ContentSearchResult(
                id=str(file.id),
                title=file.title,
                content_type=file.file_type,
                description=file.description,
                tags=file.tags,
                relevance_score=relevance_score,
                snippet=snippet,
                created_at=file.created_at
            )
            search_results.append(search_result)
        
        return search_results

    async def get_content_stats(self, tenant_id: str) -> Dict[str, Any]:
        """コンテンツ統計取得"""
        # 総ファイル数
        total_files_result = await self.db.execute(
            select(func.count(File.id)).where(
                and_(
                    File.tenant_id == tenant_id,
                    File.deleted_at.is_(None)
                )
            )
        )
        total_files = total_files_result.scalar() or 0
        
        # ステータス別ファイル数
        status_counts = {}
        for status in FileStatus:
            count_result = await self.db.execute(
                select(func.count(File.id)).where(
                    and_(
                        File.tenant_id == tenant_id,
                        File.status == status,
                        File.deleted_at.is_(None)
                    )
                )
            )
            status_counts[status.value] = count_result.scalar() or 0
        
        # 総チャンク数
        total_chunks_result = await self.db.execute(
            select(func.count(Chunk.id)).where(Chunk.tenant_id == tenant_id)
        )
        total_chunks = total_chunks_result.scalar() or 0
        
        # 総ストレージサイズ
        total_size_result = await self.db.execute(
            select(func.sum(File.size_bytes)).where(
                and_(
                    File.tenant_id == tenant_id,
                    File.deleted_at.is_(None)
                )
            )
        )
        total_size_bytes = total_size_result.scalar() or 0
        
        return {
            "total_files": total_files,
            "status_counts": status_counts,
            "total_chunks": total_chunks,
            "total_size_mb": FileUtils.get_file_size_mb(total_size_bytes),
            "file_types": {
                file_type.value: await self._get_file_type_count(tenant_id, file_type)
                for file_type in FileType
            }
        }

    async def _get_file_type_count(self, tenant_id: str, file_type: FileType) -> int:
        """ファイルタイプ別件数取得"""
        result = await self.db.execute(
            select(func.count(File.id)).where(
                and_(
                    File.tenant_id == tenant_id,
                    File.file_type == file_type,
                    File.deleted_at.is_(None)
                )
            )
        )
        return result.scalar() or 0

    async def reindex_content(self, content_id: str, tenant_id: str) -> bool:
        """コンテンツ再インデックス"""
        content = await self.get_by_id(content_id, tenant_id)
        if not content:
            return False
        
        # ステータスをPROCESSINGに更新
        content.status = FileStatus.PROCESSING
        content.error_message = None
        
        await self.db.commit()
        
        # TODO: 実際のインデックス処理を実装
        # ここでは仮に成功として処理
        
        content.status = FileStatus.INDEXED
        content.indexed_at = datetime.utcnow()
        
        await self.db.commit()
        
        BusinessLogger.log_content_action(
            content_id,
            "content_reindexed",
            str(content.uploaded_by),
            tenant_id
        )
        
        return True

    async def get_storage_usage(self, tenant_id: str) -> Dict[str, Any]:
        """ストレージ使用量取得"""
        # 総サイズ
        total_size_result = await self.db.execute(
            select(func.sum(File.size_bytes)).where(
                and_(
                    File.tenant_id == tenant_id,
                    File.deleted_at.is_(None)
                )
            )
        )
        total_size_bytes = total_size_result.scalar() or 0
        
        # TODO: テナントの制限値を取得
        limit_bytes = 100 * 1024 * 1024  # 100MB
        
        return {
            "used_bytes": total_size_bytes,
            "used_mb": FileUtils.get_file_size_mb(total_size_bytes),
            "limit_bytes": limit_bytes,
            "limit_mb": FileUtils.get_file_size_mb(limit_bytes),
            "usage_percentage": (total_size_bytes / limit_bytes) * 100 if limit_bytes > 0 else 0
        }
