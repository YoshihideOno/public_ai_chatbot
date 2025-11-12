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
from app.utils.common import StringUtils, ValidationUtils, FileUtils, DateTimeUtils
from app.utils.logging import BusinessLogger, ErrorLogger, logger
from app.services.storage_service import StorageServiceFactory
from app.core.database import AsyncSessionLocal
import asyncio
from app.core.exceptions import ConflictError
from app.services.tenant_service import TenantService
from sqlalchemy import delete


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
                logger.warning(f"無効なパラメータ: content_id={content_id}, tenant_id={tenant_id}")
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
                logger.info(f"コンテンツ取得成功: ID {content_id}")
            else:
                logger.info(f"コンテンツ未発見: ID {content_id}")
                
            return content
        except Exception as e:
            logger.error(f"コンテンツ取得エラー: {str(e)}")
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
        # プラットフォーム管理者（全テナント横断）の場合はテナント条件を外す
        if tenant_id == "system":
            query = select(File).where(
                File.deleted_at.is_(None)
            )
        else:
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

    async def check_duplicate_filename(self, file_name: str, tenant_id: str) -> bool:
        """
        ファイル名の重複チェック
        
        引数:
            file_name: チェックするファイル名
            tenant_id: テナントID
        
        戻り値:
            bool: 重複が存在する場合True、存在しない場合False
        
        例外:
            ConflictError: 重複が存在する場合
        """
        try:
            result = await self.db.execute(
                select(File).where(
                    and_(
                        File.tenant_id == tenant_id,
                        File.file_name == file_name,
                        File.deleted_at.is_(None)
                    )
                )
            )
            existing_file = result.scalar_one_or_none()
            
            if existing_file:
                raise ConflictError(f"同一ファイル名のファイルが既に存在します: {file_name}")
            
            return False
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"ファイル名重複チェックエラー: {str(e)}")
            raise

    async def create_content(self, content_data: ContentCreate, tenant_id: str, user_id: str, idempotency_key: Optional[str] = None) -> File:
        """
        コンテンツ作成
        
        引数:
            content_data: コンテンツ作成データ
            tenant_id: テナントID
            user_id: ユーザーID
        
        戻り値:
            File: 作成されたファイルオブジェクト
        
        例外:
            ConflictError: ファイル名が重複している場合
            ValueError: バリデーションエラー
        """
        # 冪等性キーが指定された場合、既存を返す
        try:
            if idempotency_key:
                from sqlalchemy import and_
                result = await self.db.execute(
                    select(File).where(
                        and_(
                            File.tenant_id == tenant_id,
                            File.metadata_json['idempotency_key'].astext == idempotency_key,
                            File.deleted_at.is_(None)
                        )
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    logger.info(f"Idempotency-Key一致の既存ファイルを返却: key={idempotency_key}, file_id={existing.id}")
                    return existing
        except Exception as e:
            logger.warning(f"Idempotencyキー照会でエラーが発生しました（処理は継続）: {str(e)}")

        # ファイル名の決定
        if content_data.file_url:
            # URLからファイル名を抽出
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(content_data.file_url)
                file_name = parsed_url.path.split('/')[-1] or f"{content_data.title}.{content_data.content_type.value.lower()}"
            except Exception:
                file_name = f"{content_data.title}.{content_data.content_type.value.lower()}"
        else:
            file_name = f"{content_data.title}.{content_data.content_type.value.lower()}"
        
        # ファイル名の重複チェック
        await self.check_duplicate_filename(file_name, tenant_id)
        
        # ファイルサイズチェックとファイル内容の準備
        file_content_bytes = None
        if content_data.file_content:
            file_content_bytes = base64.b64decode(content_data.file_content)
            file_size = len(file_content_bytes)
            if not ValidationUtils.validate_file_size(file_size):
                raise ValueError("ファイルサイズが制限を超えています")
        elif content_data.file_url:
            # URLからファイルをダウンロード
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(content_data.file_url, timeout=30.0)
                    response.raise_for_status()
                    file_content_bytes = response.content
                    file_size = len(file_content_bytes)
            except Exception as e:
                logger.error(f"URLからのファイル取得エラー: {str(e)}")
                raise ValueError(f"URLからのファイル取得に失敗しました: {str(e)}")
        else:
            file_size = 0
        
        # ストレージサービスへのファイル保存
        storage_service = StorageServiceFactory.create()
        s3_key = None
        if file_content_bytes:
            try:
                content_type = f"application/{content_data.content_type.value.lower()}"
                s3_key = await storage_service.upload_file(
                    file_content=file_content_bytes,
                    file_name=file_name,
                    tenant_id=tenant_id,
                    content_type=content_type
                )
                logger.info(f"ファイルをストレージに保存: {s3_key}")
            except Exception as e:
                logger.error(f"ストレージへのファイル保存エラー: {str(e)}")
                raise ValueError(f"ファイルの保存に失敗しました: {str(e)}")
        # ファイル内容がない場合（URLのみ）は一時的に空のキーを設定
        if not s3_key:
            s3_key = f"tenant/{tenant_id}/files/{uuid.uuid4()}"
        
        # メタデータにfile_urlやidempotency_keyを追加
        metadata = dict(content_data.metadata) if content_data.metadata else {}
        if content_data.file_url:
            metadata['file_url'] = content_data.file_url
        if idempotency_key:
            metadata['idempotency_key'] = idempotency_key
        
        # ファイル作成
        db_file = File(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=content_data.title,
            file_name=file_name,
            file_type=content_data.content_type,
            size_bytes=file_size,
            s3_key=s3_key,
            uploaded_by=user_id,
            description=content_data.description,
            tags=content_data.tags,
            metadata_json=metadata
        )
        
        self.db.add(db_file)
        await self.db.commit()
        await self.db.refresh(db_file)
        
        # 自動処理はバックグラウンドで実行（ファイル内容がある場合のみ）
        if file_content_bytes:
            try:
                # チャンク設定の決定順序:
                # 1) ContentCreate指定値 > 2) テナント設定 > 3) コード既定値
                tenant_service = TenantService(self.db)
                tenant = await tenant_service.get_by_id(tenant_id)
                tenant_settings = tenant.settings if tenant and tenant.settings else {}

                resolved_chunk_size = (
                    content_data.chunk_size
                    or tenant_settings.get('chunk_size')
                    or 1024
                )
                resolved_chunk_overlap = (
                    content_data.chunk_overlap
                    or tenant_settings.get('chunk_overlap')
                    or 200
                )

                # 即時にPROCESSINGへ更新（一覧で進行中表示）
                db_file.status = FileStatus.PROCESSING
                await self.db.commit()

                file_id_str = str(db_file.id)

                # BG開始ログ
                BusinessLogger.log_content_action(
                    file_id_str,
                    "background_started",
                    user_id,
                    tenant_id
                )

                async def _bg_process(file_id: str, tenant_id_bg: str, chunk_size_bg: int, chunk_overlap_bg: int) -> None:
                    """
                    バックグラウンドでRAGパイプラインを実行する補助関数。
                    セッションはBG専用に新規作成し、完了後自動クローズする。
                    """
                    from app.services.rag_pipeline import RAGPipeline
                    from app.models.file import FileStatus, File
                    import uuid
                    import asyncio
                    
                    logger.info(f"BG処理開始: file_id={file_id}")
                    
                    # セッションを直接コンテキストマネージャーとして使用（get_db()と同じパターン）
                    async with AsyncSessionLocal() as db_bg:
                        try:
                            # タイムアウトを設定（30分）
                            rag_pipeline = RAGPipeline(db_bg)
                            await asyncio.wait_for(
                                rag_pipeline.process_file(
                                    file_id,
                                    tenant_id_bg,
                                    chunk_size=chunk_size_bg,
                                    chunk_overlap=chunk_overlap_bg
                                ),
                                timeout=1800.0  # 30分
                            )
                            logger.info(f"BG処理完了: file_id={file_id}")
                        except asyncio.TimeoutError:
                            logger.error(f"BG処理タイムアウト: file_id={file_id}")
                            # タイムアウト時はステータスをFAILEDに更新
                            try:
                                result = await db_bg.execute(
                                    select(File).where(File.id == uuid.UUID(file_id))
                                )
                                file_obj = result.scalar_one_or_none()
                                if file_obj:
                                    file_obj.status = FileStatus.FAILED
                                    file_obj.error_message = "処理がタイムアウトしました（30分）"
                                    await db_bg.commit()
                                    
                                    # メール通知を送信（非同期、エラーはログのみ）
                                    try:
                                        from app.services.email_service import EmailService
                                        from app.models.user import User
                                        
                                        user_result = await db_bg.execute(
                                            select(User).where(User.id == file_obj.uploaded_by)
                                        )
                                        user = user_result.scalar_one_or_none()
                                        
                                        if user and user.email:
                                            await EmailService.send_content_processing_failure_email(
                                                to_email=user.email,
                                                username=user.username,
                                                file_title=file_obj.title,
                                                file_name=file_obj.file_name,
                                                error_message="処理がタイムアウトしました（30分）"
                                            )
                                    except Exception as email_error:
                                        logger.error(f"メール送信エラー（タイムアウト）: {str(email_error)}")
                            except Exception as update_error:
                                logger.error(f"タイムアウト時のステータス更新エラー: file_id={file_id}, error={str(update_error)}", exc_info=True)
                                await db_bg.rollback()
                        except Exception as e:
                            logger.error(f"BG処理エラー: file_id={file_id}, error={str(e)}", exc_info=True)
                            # エラー時はステータスをFAILEDに更新
                            try:
                                result = await db_bg.execute(
                                    select(File).where(File.id == uuid.UUID(file_id))
                                )
                                file_obj = result.scalar_one_or_none()
                                if file_obj:
                                    file_obj.status = FileStatus.FAILED
                                    file_obj.error_message = f"処理エラー: {str(e)}"
                                    await db_bg.commit()
                                    
                                    # メール通知を送信（非同期、エラーはログのみ）
                                    try:
                                        from app.services.email_service import EmailService
                                        from app.models.user import User
                                        
                                        user_result = await db_bg.execute(
                                            select(User).where(User.id == file_obj.uploaded_by)
                                        )
                                        user = user_result.scalar_one_or_none()
                                        
                                        if user and user.email:
                                            await EmailService.send_content_processing_failure_email(
                                                to_email=user.email,
                                                username=user.username,
                                                file_title=file_obj.title,
                                                file_name=file_obj.file_name,
                                                error_message=f"処理エラー: {str(e)}"
                                            )
                                    except Exception as email_error:
                                        logger.error(f"メール送信エラー（処理エラー）: {str(email_error)}")
                            except Exception as update_error:
                                logger.error(f"ステータス更新エラー: file_id={file_id}, error={str(update_error)}", exc_info=True)
                                await db_bg.rollback()

                asyncio.create_task(
                    _bg_process(
                        file_id_str,
                        tenant_id,
                        resolved_chunk_size,
                        resolved_chunk_overlap
                    )
                )
            except Exception as e:
                logger.error(f"BG起動エラー: file_id={db_file.id}, error={str(e)}")
        
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
        
        content.updated_at = DateTimeUtils.now()
        
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
        """
        コンテンツ削除（ソフトデリート）
        
        ストレージからもファイルを削除し、関連チャンクおよびベクターストアのベクトルも削除します。
        いずれかの削除に失敗してもログを記録して処理を継続します（最終的にDB側はソフトデリート）。
        """
        content = await self.get_by_id(content_id, tenant_id)
        if not content:
            return False
        
        # ストレージからファイルを削除（失敗してもログのみで継続）
        if content.s3_key:
            try:
                storage_service = StorageServiceFactory.create()
                deleted = await storage_service.delete_file(content.s3_key)
                if deleted:
                    logger.info(f"ストレージからファイルを削除: {content.s3_key}")
                else:
                    logger.warning(f"ストレージファイルの削除に失敗（ファイルが存在しない可能性）: {content.s3_key}")
            except Exception as e:
                logger.error(f"ストレージファイル削除エラー: {str(e)}, s3_key={content.s3_key}")
                # エラーが発生してもDB削除は継続

        # ベクターストアから削除（tenant_id + file_id 指定）
        try:
            from app.services.vector_db_service import VectorDBService
            vdb = VectorDBService()
            ok = await vdb.delete_by_file(tenant_id, content_id)
            if ok:
                logger.info(f"ベクターストアからベクトル削除完了: tenant_id={tenant_id}, file_id={content_id}")
            else:
                logger.warning(f"ベクターストアからの削除に失敗: tenant_id={tenant_id}, file_id={content_id}")
        except Exception as e:
            logger.error(f"ベクターストア削除エラー: {str(e)}")

        # チャンクをDBから削除（ファイルIDで一括）
        try:
            await self.db.execute(
                delete(Chunk).where(
                    and_(
                        Chunk.file_id == content_id,
                        Chunk.tenant_id == tenant_id
                    )
                )
            )
            logger.info(f"チャンクをDBから削除: file_id={content_id}")
        except Exception as e:
            logger.error(f"チャンク削除エラー: file_id={content_id}, error={str(e)}")

        content.deleted_at = DateTimeUtils.now()
        
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
        content.indexed_at = DateTimeUtils.now()
        
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
