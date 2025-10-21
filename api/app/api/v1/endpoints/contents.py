from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.content import (
    Content, ContentCreate, ContentUpdate, ContentWithChunks,
    Chunk, ChunkCreate, ChunkUpdate, ContentSearchParams,
    ContentSearchResult
)
from app.schemas.user import User
from app.services.content_service import ContentService
from app.api.v1.deps import (
    get_current_user, 
    require_admin_role,
    get_tenant_from_user
)
from app.models.user import UserRole
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError, 
    TenantAccessDeniedError
)
from app.utils.logging import BusinessLogger, ErrorLogger
from app.utils.common import PaginationUtils, ValidationUtils

router = APIRouter()


@router.get("/", response_model=List[Content])
async def get_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    file_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ一覧取得"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    # ファイルタイプの変換
    file_type_enum = None
    if file_type:
        try:
            from app.models.file import FileType
            file_type_enum = FileType(file_type.upper())
        except ValueError:
            raise ValidationError(f"無効なファイルタイプ: {file_type}")
    
    # ステータスの変換
    status_enum = None
    if status:
        try:
            from app.models.file import FileStatus
            status_enum = FileStatus(status.upper())
        except ValueError:
            raise ValidationError(f"無効なステータス: {status}")
    
    contents = await content_service.get_all_contents(
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        file_type=file_type_enum,
        status=status_enum,
        search_query=search
    )
    
    BusinessLogger.log_user_action(
        current_user.id,
        "list_contents",
        "contents",
        tenant_id=tenant_id
    )
    
    return contents


@router.post("/", response_model=Content)
async def create_content(
    content_data: ContentCreate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ作成"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    try:
        content = await content_service.create_content(
            content_data=content_data,
            tenant_id=tenant_id,
            user_id=str(current_user.id)
        )
        
        BusinessLogger.log_user_action(
            current_user.id,
            "create_content",
            "content",
            tenant_id=tenant_id
        )
        
        return content
        
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """ファイルアップロード"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    # ファイルサイズチェック
    file_content = await file.read()
    if not ValidationUtils.validate_file_size(len(file_content)):
        raise ValidationError("ファイルサイズが制限を超えています")
    
    # ファイルタイプチェック
    file_extension = file.filename.split('.')[-1].upper() if '.' in file.filename else ''
    try:
        from app.models.file import FileType
        file_type = FileType(file_extension)
    except ValueError:
        raise ValidationError(f"サポートされていないファイルタイプ: {file_extension}")
    
    # Base64エンコード
    import base64
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # タグの処理
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # コンテンツデータ作成
    content_data = ContentCreate(
        title=title or file.filename.split('.')[0],
        content_type=file_type,
        description=description,
        tags=tag_list,
        file_content=file_content_b64
    )
    
    try:
        content = await content_service.create_content(
            content_data=content_data,
            tenant_id=tenant_id,
            user_id=str(current_user.id)
        )
        
        BusinessLogger.log_user_action(
            current_user.id,
            "upload_file",
            "content",
            tenant_id=tenant_id
        )
        
        return {
            "message": "ファイルがアップロードされました",
            "content": content
        }
        
    except ValueError as e:
        raise ValidationError(str(e))


@router.get("/{content_id}", response_model=ContentWithChunks)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ詳細取得"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    content = await content_service.get_by_id(content_id, tenant_id)
    if not content:
        raise ResourceNotFoundError("Content")
    
    # チャンク情報も取得
    chunks = await content_service.get_content_chunks(content_id, tenant_id)
    
    BusinessLogger.log_user_action(
        current_user.id,
        "get_content",
        "content",
        tenant_id=tenant_id
    )
    
    return ContentWithChunks(
        **content.__dict__,
        chunks=[chunk.__dict__ for chunk in chunks],
        chunk_count=len(chunks)
    )


@router.put("/{content_id}", response_model=Content)
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ更新"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    content = await content_service.update_content(
        content_id=content_id,
        content_update=content_update,
        tenant_id=tenant_id
    )
    
    if not content:
        raise ResourceNotFoundError("Content")
    
    BusinessLogger.log_user_action(
        current_user.id,
        "update_content",
        "content",
        tenant_id=tenant_id
    )
    
    return content


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ削除"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    success = await content_service.delete_content(content_id, tenant_id)
    if not success:
        raise ResourceNotFoundError("Content")
    
    BusinessLogger.log_user_action(
        current_user.id,
        "delete_content",
        "content",
        tenant_id=tenant_id
    )
    
    return {"message": "コンテンツが削除されました"}


@router.post("/{content_id}/reindex")
async def reindex_content(
    content_id: str,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ再インデックス"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    success = await content_service.reindex_content(content_id, tenant_id)
    if not success:
        raise ResourceNotFoundError("Content")
    
    BusinessLogger.log_user_action(
        current_user.id,
        "reindex_content",
        "content",
        tenant_id=tenant_id
    )
    
    return {"message": "再インデックスが開始されました"}


@router.get("/{content_id}/chunks", response_model=List[Chunk])
async def get_content_chunks(
    content_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツのチャンク一覧取得"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    chunks = await content_service.get_content_chunks(
        content_id=content_id,
        tenant_id=tenant_id,
        skip=skip,
        limit=limit
    )
    
    BusinessLogger.log_user_action(
        current_user.id,
        "get_content_chunks",
        "chunks",
        tenant_id=tenant_id
    )
    
    return chunks


@router.post("/{content_id}/chunks", response_model=Chunk)
async def create_chunk(
    content_id: str,
    chunk_data: ChunkCreate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """チャンク作成"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    # ファイルIDを設定
    chunk_data.file_id = content_id
    
    try:
        chunk = await content_service.create_chunk(chunk_data, tenant_id)
        
        BusinessLogger.log_user_action(
            current_user.id,
            "create_chunk",
            "chunk",
            tenant_id=tenant_id
        )
        
        return chunk
        
    except ValueError as e:
        raise ValidationError(str(e))


@router.put("/chunks/{chunk_id}", response_model=Chunk)
async def update_chunk(
    chunk_id: str,
    chunk_update: ChunkUpdate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """チャンク更新"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    chunk = await content_service.update_chunk(
        chunk_id=chunk_id,
        chunk_update=chunk_update,
        tenant_id=tenant_id
    )
    
    if not chunk:
        raise ResourceNotFoundError("Chunk")
    
    BusinessLogger.log_user_action(
        current_user.id,
        "update_chunk",
        "chunk",
        tenant_id=tenant_id
    )
    
    return chunk


@router.delete("/chunks/{chunk_id}")
async def delete_chunk(
    chunk_id: str,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """チャンク削除"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    success = await content_service.delete_chunk(chunk_id, tenant_id)
    if not success:
        raise ResourceNotFoundError("Chunk")
    
    BusinessLogger.log_user_action(
        current_user.id,
        "delete_chunk",
        "chunk",
        tenant_id=tenant_id
    )
    
    return {"message": "チャンクが削除されました"}


@router.post("/search", response_model=List[ContentSearchResult])
async def search_contents(
    search_params: ContentSearchParams,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ検索"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    results = await content_service.search_contents(search_params, tenant_id)
    
    BusinessLogger.log_user_action(
        current_user.id,
        "search_contents",
        "content_search",
        tenant_id=tenant_id
    )
    
    return results


@router.get("/stats/summary")
async def get_content_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ統計取得"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    stats = await content_service.get_content_stats(tenant_id)
    
    BusinessLogger.log_user_action(
        current_user.id,
        "get_content_stats",
        "content_stats",
        tenant_id=tenant_id
    )
    
    return stats


@router.get("/stats/storage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ストレージ使用量取得"""
    tenant_id = get_tenant_from_user(current_user)
    content_service = ContentService(db)
    
    usage = await content_service.get_storage_usage(tenant_id)
    
    BusinessLogger.log_user_action(
        current_user.id,
        "get_storage_usage",
        "storage_usage",
        tenant_id=tenant_id
    )
    
    return usage
