from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File as FastAPIFile, Request
from fastapi.responses import StreamingResponse, Response
from io import StringIO
import csv
from datetime import datetime as dt
from urllib.parse import quote
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
)
from app.models.user import UserRole
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError, 
    TenantAccessDeniedError, ConflictError
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
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"  # Platform admin can access all tenants
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
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
    
    files = await content_service.get_all_contents(
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        file_type=file_type_enum,
        status=status_enum,
        search_query=search
    )
    
    # FileモデルをContentスキーマに変換
    from app.schemas.content import Content
    contents = []
    for file in files:
        content_dict = {
            'id': str(file.id),
            'tenant_id': str(file.tenant_id),
            'title': file.title,
            'content_type': file.file_type.value,
            'description': file.description,
            'tags': file.tags if file.tags else [],
            'metadata': file.metadata_json if file.metadata_json else {},
            'file_name': file.file_name,
            'file_size': file.size_bytes,
            'status': file.status.value,
            'uploaded_at': file.uploaded_at,
            'indexed_at': file.indexed_at,
            'created_at': file.created_at,
            'updated_at': file.updated_at,
        }
        contents.append(Content(**content_dict))
    
    # コンテンツ一覧はダッシュボード表示用の参照系GETのため、監査ログには記録しない
    return contents


@router.post("/", response_model=Content)
async def create_content(
    content_data: ContentCreate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ作成"""
    # ファイルが必須であることを確認
    if not content_data.file_content and not content_data.file_url:
        raise ValidationError("ファイルコンテンツまたはファイルURLが必須です")
    
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    try:
        # Idempotency-Key（任意）の取得
        idempotency_key = request.headers.get("Idempotency-Key")
        content = await content_service.create_content(
            content_data=content_data,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            idempotency_key=idempotency_key
        )
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "create_content",
            "content",
            tenant_id=tenant_id,
            request=request,
            resource_id=str(content.id)
        )
        
        # BG処理開始後は202 Acceptedで即時返却（Locationヘッダ付与）
        from fastapi.responses import JSONResponse
        headers = {
            "Location": f"/api/v1/contents/{content.id}"
        }
        payload = {
            "id": str(content.id),
            "status": "PROCESSING",
            "message": "処理を開始しました。後で一覧で完了をご確認ください"
        }
        return JSONResponse(status_code=202, content=payload, headers=headers)
        
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    ファイルアップロード（テストモード: 3つの異なるaddRandomSuffixパラメータ形式でアップロード）
    
    注意: 現在はテストモードとして、3つの異なるパラメータ形式（"true"、bool値のTrue、数値の1）で
    アップロードします。後続の処理（RAGパイプライン）は実行しません。
    正しいパラメータが判明したら、このコードを元に戻してください。
    """
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    
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
    
    # テストモード: 3つの異なるパラメータ形式でアップロード
    from app.services.storage_service import StorageServiceFactory
    
    # 元のファイル名を取得（拡張子を除く）
    original_filename_without_ext = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
    
    # テストするパラメータ形式: "true"、bool値のTrue、数値の1
    # 逆の可能性を確認するため、true系のパラメータをテスト
    test_param_configs = [
        ("true", "文字列のtrue"),
        (True, "bool値のTrue"),
        (1, "数値の1"),
    ]
    
    storage_service = StorageServiceFactory.create()
    results = []
    
    for param_value, param_description in test_param_configs:
        try:
            # ファイル名にパラメータ名を含める（識別のため）
            if param_value is True:
                param_str = "True"
            elif param_value == 1:
                param_str = "1"
            else:
                param_str = str(param_value)
            
            test_filename = f"{original_filename_without_ext}_param_{param_str}.{file_ext}"
            
            # ストレージに直接アップロード（DBには保存しない、後続処理も実行しない）
            storage_key = await storage_service.upload_file(
                file_content=file_content,
                file_name=test_filename,
                tenant_id=tenant_id or "test",
                content_type=f"application/{file_ext}",
                add_random_suffix_param=param_value
            )
            
            # ストレージキーからファイル名部分を抽出
            actual_filename = storage_key.split('/')[-1] if '/' in storage_key else storage_key
            suffix_added = actual_filename != test_filename
            
            results.append({
                "param_value": str(param_value) if param_value is not True else "True",
                "param_description": param_description,
                "requested_filename": test_filename,
                "actual_storage_key": storage_key,
                "actual_filename": actual_filename,
                "suffix_added": suffix_added,
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "param_value": str(param_value) if param_value is not True else "True",
                "param_description": param_description,
                "requested_filename": test_filename if 'test_filename' in locals() else "N/A",
                "actual_storage_key": None,
                "suffix_added": None,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "message": "テストモード: 3つの異なるパラメータ形式でアップロードしました（後続処理は実行していません）",
        "original_filename": file.filename,
        "file_size": len(file_content),
        "results": results,
        "summary": {
            "total_tests": len(test_param_configs),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "no_suffix": [r for r in results if r.get("suffix_added") is False],
        }
    }


@router.get("/{content_id}", response_model=ContentWithChunks)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ詳細取得"""
    # content_idが'upload'の場合は、新規作成モードとして404を返す
    if content_id == 'upload':
        raise ResourceNotFoundError("Content")
    
    # UUIDのバリデーション
    try:
        import uuid
        uuid.UUID(content_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なコンテンツIDです"
        )
    
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    
    content_service = ContentService(db)
    
    content = await content_service.get_by_id(content_id, tenant_id)
    if not content:
        raise ResourceNotFoundError("Content")
    
    # チャンク情報も取得
    chunks = await content_service.get_content_chunks(content_id, tenant_id)
    
    # Pydanticスキーマ経由で安全に整形（__dict__の直接展開は関係属性を含み衝突の原因となる）
    from app.schemas.content import ContentInDB
    base = ContentInDB.from_orm(content).dict()
    # チャンクはORMモデルの属性名をスキーマに合わせてマッピング
    chunk_items = []
    for c in chunks:
        chunk_items.append({
            "id": str(c.id),
            "file_id": str(c.file_id),
            "tenant_id": str(c.tenant_id),
            "chunk_index": c.chunk_index,
            "content": c.chunk_text,
            "metadata": c.metadata_json or {},
            "created_at": c.created_at,
        })
    base["chunks"] = chunk_items
    base["chunk_count"] = len(chunk_items)
    # コンテンツ詳細取得は参照系GETのため、監査ログには記録しない
    return ContentWithChunks(**base)


@router.put("/{content_id}", response_model=Content)
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ更新"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    content = await content_service.update_content(
        content_id=content_id,
        content_update=content_update,
        tenant_id=tenant_id
    )
    
    if not content:
        raise ResourceNotFoundError("Content")
    
    # コンテンツ更新を監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "update_content",
        "content",
        tenant_id=tenant_id,
        request=request,
        resource_id=content_id
    )
    
    # スキーマに合わせて整形して返却
    from app.schemas.content import Content as ContentSchema
    return ContentSchema.from_orm(content)


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ削除"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    success = await content_service.delete_content(content_id, tenant_id)
    if not success:
        raise ResourceNotFoundError("Content")
    
    # コンテンツ削除を監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "delete_content",
        "content",
        tenant_id=tenant_id,
        request=request,
        resource_id=content_id
    )
    
    return {"message": "コンテンツが削除されました"}


@router.get("/{content_id}/download")
async def download_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """元ファイルのダウンロード
    認証済みユーザーに対し、テナント境界をチェックしたうえで元ファイルのバイナリを返却する。
    Content-Disposition を付与してファイルダウンロードさせる。
    """
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None

    content_service = ContentService(db)

    file_obj = await content_service.get_by_id(content_id, tenant_id)
    if not file_obj:
        raise ResourceNotFoundError("Content")

    if not getattr(file_obj, 's3_key', None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ファイルが存在しません")

    # ストレージから取得
    from app.services.storage_service import StorageServiceFactory
    try:
        storage = StorageServiceFactory.create()
        file_bytes = await storage.get_file(file_obj.s3_key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ファイル取得に失敗しました")
    
    # Content-Type 推定
    mime_map = {
        'PDF': 'application/pdf',
        'HTML': 'text/html; charset=utf-8',
        'MD': 'text/markdown; charset=utf-8',
        'CSV': 'text/csv; charset=utf-8',
        'TXT': 'text/plain; charset=utf-8',
    }
    content_type = mime_map.get(file_obj.file_type.value if getattr(file_obj, 'file_type', None) else 'TXT', 'application/octet-stream')
    
    # 元ファイルのダウンロード操作は重要なイベントのため、監査ログの記録を維持する
    BusinessLogger.log_user_action(
        str(current_user.id),
        "download_content",
        "content_download",
        tenant_id=tenant_id
    )
    
    # ファイル名をRFC 5987形式でエンコード（日本語対応）
    encoded_filename = quote(file_obj.file_name, safe='')
    headers = {
        "Content-Disposition": f"attachment; filename=\"{file_obj.file_name}\"; filename*=UTF-8''{encoded_filename}"
    }
    return Response(content=file_bytes, media_type=content_type, headers=headers)


@router.post("/{content_id}/reindex")
async def reindex_content(
    content_id: str,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ再インデックス"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    success = await content_service.reindex_content(content_id, tenant_id)
    if not success:
        raise ResourceNotFoundError("Content")
    
    # コンテンツ再インデックスを監査ログに記録
    BusinessLogger.log_user_action(
        str(current_user.id),
        "reindex_content",
        "content",
        tenant_id=tenant_id,
        request=request,
        resource_id=content_id
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
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    chunks = await content_service.get_content_chunks(
        content_id=content_id,
        tenant_id=tenant_id,
        skip=skip,
        limit=limit
    )
    
    # チャンク一覧取得は参照系GETのため、監査ログには記録しない
    return chunks


@router.get("/actions/export")
async def export_contents(
    format: str = Query("csv"),
    file_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コンテンツ一覧エクスポート（CSV/JSON）
    現在のフィルタ条件（file_type/status/search）を反映した一覧をエクスポートする。
    """
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )

    # フィルタの列挙値変換
    file_type_enum = None
    if file_type:
        try:
            from app.models.file import FileType
            file_type_enum = FileType(file_type.upper())
        except ValueError:
            raise ValidationError(f"無効なファイルタイプ: {file_type}")
    status_enum = None
    if status:
        try:
            from app.models.file import FileStatus
            status_enum = FileStatus(status.upper())
        except ValueError:
            raise ValidationError(f"無効なステータス: {status}")

    content_service = ContentService(db)
    files = await content_service.get_all_contents(
        tenant_id=tenant_id,
        skip=0,
        limit=1000,
        file_type=file_type_enum,
        status=status_enum,
        search_query=search
    )
    
    # エクスポート用データ作成（一覧表示フィールド）
    rows = []
    for f in files:
        rows.append({
            "id": str(f.id),
            "title": f.title,
            "file_name": f.file_name,
            "file_type": f.file_type.value if f.file_type else None,
            "size_bytes": f.size_bytes,
            "status": f.status.value if f.status else None,
            "chunk_count": getattr(f, 'chunk_count', None),  # 取得不可の場合はNone
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
            "indexed_at": f.indexed_at.isoformat() if f.indexed_at else None,
        })
    
    # エクスポート操作はユーザーによる明示的なデータ取得のため、監査ログ記録を維持する
    BusinessLogger.log_user_action(
        str(current_user.id),
        "export_contents",
        "contents_export",
        tenant_id=tenant_id if tenant_id != "system" else None
    )
    
    timestamp = dt.utcnow().strftime('%Y%m%d_%H%M%S')

    if format.lower() == 'json':
        import json
        payload = json.dumps(rows, ensure_ascii=False)
        headers = {
            "Content-Disposition": f"attachment; filename=\"contents_{timestamp}.json\""
        }
        return Response(content=payload.encode('utf-8'), media_type='application/json; charset=utf-8', headers=headers)

    if format.lower() != 'csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="formatはcsvまたはjsonのみ対応しています")

    # CSV作成（UTF-8, BOMなし）
    output = StringIO()
    fieldnames = ["id", "title", "file_name", "file_type", "size_bytes", "status", "chunk_count", "uploaded_at", "indexed_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    csv_bytes = output.getvalue().encode('utf-8')
    headers = {
        "Content-Disposition": f"attachment; filename=\"contents_{timestamp}.csv\""
    }
    return Response(content=csv_bytes, media_type='text/csv; charset=utf-8', headers=headers)


@router.post("/{content_id}/chunks", response_model=Chunk)
async def create_chunk(
    content_id: str,
    chunk_data: ChunkCreate,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """チャンク作成"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    # ファイルIDを設定
    chunk_data.file_id = content_id
    
    try:
        chunk = await content_service.create_chunk(chunk_data, tenant_id)
        
        BusinessLogger.log_user_action(
            str(current_user.id),
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
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """チャンク更新"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    chunk = await content_service.update_chunk(
        chunk_id=chunk_id,
        chunk_update=chunk_update,
        tenant_id=tenant_id
    )
    
    if not chunk:
        raise ResourceNotFoundError("Chunk")
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "update_chunk",
        "chunk",
        tenant_id=tenant_id
    )
    
    return chunk


@router.delete("/chunks/{chunk_id}")
async def delete_chunk(
    chunk_id: str,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """チャンク削除"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    success = await content_service.delete_chunk(chunk_id, tenant_id)
    if not success:
        raise ResourceNotFoundError("Chunk")
    
    BusinessLogger.log_user_action(
        str(current_user.id),
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
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    results = await content_service.search_contents(search_params, tenant_id)
    
    BusinessLogger.log_user_action(
        str(current_user.id),
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
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    stats = await content_service.get_content_stats(tenant_id)
    
    # コンテンツ統計はダッシュボード表示用の参照系GETのため、監査ログには記録しない
    return stats


@router.get("/stats/storage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ストレージ使用量取得"""
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = None
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    content_service = ContentService(db)
    
    usage = await content_service.get_storage_usage(tenant_id)
    
    # ストレージ使用量取得は参照系GETのため、監査ログには記録しない
    return usage


@router.post("/test-upload-params")
async def test_upload_params(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    テスト用エンドポイント: 同じファイルを複数のaddRandomSuffixパラメータ形式でアップロードし、
    どの形式でサフィックスが付加されないかを確認する
    
    注意: このエンドポイントはテスト目的のため、本番環境では無効化することを推奨
    """
    from app.core.config import settings
    from app.services.storage_service import StorageServiceFactory
    import uuid
    import base64
    
    # テスト環境でのみ有効（本番環境では無効化）
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このエンドポイントは本番環境では使用できません"
        )
    
    # tenant_idの取得
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "test"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else "test"
    
    # ファイル内容を読み込み
    file_content = await file.read()
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
    
    # テスト用のベースファイル名
    test_id = str(uuid.uuid4())[:8]
    base_filename = f"test_file_{test_id}.{file_extension}"
    
    # テストするパラメータ形式
    # ユーザーの要望: "false"、bool値のFalse、数値の0の3種類
    test_params = [
        ("false", "文字列のfalse"),
        (False, "bool値のFalse"),
        (0, "数値の0"),
    ]
    
    storage_service = StorageServiceFactory.create()
    results = []
    
    # 元のファイル名を取得（拡張子を除く）
    original_filename_without_ext = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
    
    for param_value, param_description in test_params:
        try:
            # ファイル名にパラメータ名を含める（識別のため）
            # 例: "service_info_param_false.md", "service_info_param_False.md", "service_info_param_0.md"
            if param_value is False:
                param_str = "False"  # bool値のFalseを識別
            elif param_value == 0:
                param_str = "0"  # 数値の0を識別
            else:
                param_str = str(param_value)
            
            test_filename = f"{original_filename_without_ext}_param_{param_str}.{file_extension}"
            
            # アップロード
            storage_key = await storage_service.upload_file(
                file_content=file_content,
                file_name=test_filename,
                tenant_id=tenant_id,
                content_type=f"application/{file_extension}",
                add_random_suffix_param=param_value
            )
            
            # 結果を記録
            # ストレージキーからファイル名部分を抽出（tenant_id/file_name形式）
            actual_filename = storage_key.split('/')[-1] if '/' in storage_key else storage_key
            # サフィックスが付加されているかどうかを判定
            # 実際のファイル名が要求したファイル名と完全に一致する場合は、サフィックスなし
            suffix_added = actual_filename != test_filename
            
            results.append({
                "param_value": param_value,
                "param_description": param_description,
                "requested_filename": test_filename,
                "actual_storage_key": storage_key,
                "actual_filename": actual_filename,
                "suffix_added": suffix_added,
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "param_value": param_value,
                "param_description": param_description,
                "requested_filename": test_filename if 'test_filename' in locals() else "N/A",
                "actual_storage_key": None,
                "suffix_added": None,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "test_id": test_id,
        "base_filename": base_filename,
        "file_size": len(file_content),
        "results": results,
        "summary": {
            "total_tests": len(test_params),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "no_suffix": [r for r in results if r.get("suffix_added") is False],
        }
    }
