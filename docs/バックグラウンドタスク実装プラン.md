# BackgroundTasksを使った実装プラン

## 概要
FastAPIの`BackgroundTasks`を使用して、ファイルアップロード後の処理を非同期で実行する実装プランです。
現在の`asyncio.create_task()`方式から、FastAPI標準の`BackgroundTasks`方式へ移行します。

## メリット
1. **FastAPI標準の仕組み**: レスポンス返却後に確実に実行される
2. **リクエスト終了後も実行**: レスポンスを返した後もタスクが継続
3. **エラーハンドリング**: FastAPIが自動的にエラーをキャッチしてログに記録
4. **リクエストコンテキスト**: リクエストスコープ内で実行されるため、適切なクリーンアップが保証される

## 実装ステップ

### ステップ1: バックグラウンド処理関数を独立させる
`content_service.py`の`_bg_process`関数を、エンドポイントから直接呼び出せる独立した関数に変更します。

**ファイル**: `api/app/services/content_service.py`

```python
async def process_file_background(
    file_id: str,
    tenant_id: str,
    chunk_size: int,
    chunk_overlap: int
) -> None:
    """
    バックグラウンドでファイル処理を実行する関数。
    FastAPIのBackgroundTasksから呼び出される。
    
    引数:
        file_id: 処理するファイルID
        tenant_id: テナントID
        chunk_size: チャンクサイズ
        chunk_overlap: チャンクオーバーラップ
    """
    from app.services.rag_pipeline import RAGPipeline
    from app.models.file import FileStatus, File
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    import uuid
    
    # セッションを直接コンテキストマネージャーとして使用
    async with AsyncSessionLocal() as db_bg:
        try:
            rag_pipeline = RAGPipeline(db_bg)
            await rag_pipeline.process_file(
                file_id,
                tenant_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
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
            except Exception as update_error:
                logger.error(f"ステータス更新エラー: file_id={file_id}, error={str(update_error)}", exc_info=True)
                await db_bg.rollback()
```

### ステップ2: ContentService.create_contentを修正
`create_content`メソッドから`asyncio.create_task`を削除し、バックグラウンド処理の起動を呼び出し側に委譲します。

**ファイル**: `api/app/services/content_service.py`

```python
# create_contentメソッド内で、以下の部分を削除:
# - async def _bg_process(...) の定義
# - asyncio.create_task(...) の呼び出し

# 代わりに、バックグラウンド処理の起動が必要かどうかのフラグを返すか、
# または呼び出し側でBackgroundTasksを登録するように変更
```

**オプションA**: バックグラウンド処理関数を返す
```python
# create_contentの戻り値に、バックグラウンド処理の情報を含める
return {
    "file": db_file,
    "background_task": {
        "file_id": str(db_file.id),
        "tenant_id": tenant_id,
        "chunk_size": resolved_chunk_size,
        "chunk_overlap": resolved_chunk_overlap
    }
}
```

**オプションB**: バックグラウンド処理関数を直接呼び出し可能にする
```python
# create_contentはFileオブジェクトのみを返し、
# バックグラウンド処理はエンドポイント側で登録する
```

### ステップ3: upload_fileエンドポイントを修正
`upload_file`エンドポイントに`BackgroundTasks`を追加し、バックグラウンド処理を登録します。

**ファイル**: `api/app/api/v1/endpoints/contents.py`

```python
from fastapi import BackgroundTasks
from app.services.content_service import process_file_background

@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """ファイルアップロード"""
    # ... 既存のコード（ファイルアップロード処理） ...
    
    # コンテンツ作成
    db_file = await content_service.create_content(
        content_data,
        tenant_id,
        str(current_user.id)
    )
    
    # ファイル内容がある場合、バックグラウンド処理を登録
    if file_content_bytes:
        # チャンク設定の決定
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_by_id(tenant_id)
        tenant_settings = tenant.settings if tenant and tenant.settings else {}
        
        resolved_chunk_size = (
            chunk_size
            or tenant_settings.get('chunk_size')
            or 1024
        )
        resolved_chunk_overlap = (
            chunk_overlap
            or tenant_settings.get('chunk_overlap')
            or 200
        )
        
        # ステータスをPROCESSINGに更新
        db_file.status = FileStatus.PROCESSING
        await db.commit()
        
        # バックグラウンドタスクを登録
        background_tasks.add_task(
            process_file_background,
            str(db_file.id),
            tenant_id,
            resolved_chunk_size,
            resolved_chunk_overlap
        )
        
        # BG開始ログ
        BusinessLogger.log_content_action(
            str(db_file.id),
            "background_started",
            str(current_user.id),
            tenant_id
        )
    
    return ContentResponse(...)
```

### ステップ4: インポートの追加
必要なインポートを追加します。

**ファイル**: `api/app/api/v1/endpoints/contents.py`

```python
from fastapi import BackgroundTasks
from app.services.content_service import process_file_background
from app.services.tenant_service import TenantService
from app.models.file import FileStatus
```

**ファイル**: `api/app/services/content_service.py`

```python
# process_file_background関数をエクスポート（モジュールレベルで定義）
```

## 実装の注意点

1. **セッション管理**: バックグラウンドタスク内では必ず新しいDBセッションを作成する
2. **エラーハンドリング**: バックグラウンドタスク内のエラーは適切にログに記録し、ファイルステータスを更新する
3. **ログ記録**: バックグラウンドタスクの開始・終了・エラーを構造化ログで記録する
4. **テスト**: バックグラウンドタスクが正しく実行されることをテストする

## 移行手順

1. ステップ1: `process_file_background`関数を`content_service.py`に追加
2. ステップ2: `create_content`から`asyncio.create_task`を削除
3. ステップ3: `upload_file`エンドポイントに`BackgroundTasks`を追加
4. ステップ4: テスト実行して動作確認
5. ステップ5: `asyncio`のインポートを削除（不要になった場合）

## 期待される効果

- **安定性向上**: FastAPI標準の仕組みにより、より確実にバックグラウンド処理が実行される
- **エラーハンドリング改善**: FastAPIが自動的にエラーをキャッチし、適切にログに記録
- **コードの明確性**: エンドポイント側でバックグラウンド処理が明示的に登録されるため、処理フローが明確になる
- **デバッグ容易性**: バックグラウンドタスクの実行状況がより明確に追跡可能

