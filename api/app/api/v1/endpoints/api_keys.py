"""
APIキー管理エンドポイント

このファイルはAPIキー管理に関するAPIエンドポイントを定義します。
APIキーの登録・更新・削除・取得機能を提供します。

主な機能:
- APIキーの登録・更新・削除
- APIキー一覧の取得
- プロバイダー・モデル情報の取得
- テナント管理者専用の機能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.schemas.api_key import (
    ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse, ApiKeyListResponse,
    ProviderModelListResponse, ProviderModelInfo
)
from app.services.api_key_service import ApiKeyService
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from app.api.v1.deps import get_current_user, require_admin_role, require_operator_or_above, require_admin_or_auditor, require_tenant_user
from app.models.user import User
from app.core.exceptions import (
    ApiKeyNotFoundError, ValidationError, BusinessLogicError
)
from app.utils.logging import BusinessLogger, ErrorLogger, logger
from app.core.constants import ApiKeySettings

router = APIRouter()


def translate_validation_error(errors: List[dict]) -> str:
    """
    Pydanticバリデーションエラーメッセージを日本語に変換
    
    引数:
        errors: Pydanticのバリデーションエラーリスト
    戻り値:
        str: 日本語化されたエラーメッセージ
    """
    messages = []
    field_translations = {
        "provider": "プロバイダー",
        "api_key": "APIキー",
        "model": "モデル"
    }
    error_type_translations = {
        "missing": "が入力されていません",
        "value_error": "の値が不正です",
        "type_error": "の型が正しくありません",
        "string_too_short": "が短すぎます（最低{min_length}文字必要です）",
        "string_too_long": "が長すぎます（最大{max_length}文字までです）",
    }
    
    for error in errors:
        field = error.get("loc", ["unknown"])[-1]
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        
        field_jp = field_translations.get(str(field), field)
        
        if error_type == "value_error.missing":
            messages.append(f"{field_jp}が入力されていません")
        elif error_type == "value_error.str.regex":
            messages.append(f"{field_jp}の形式が正しくありません")
        elif "string_too_short" in error_type or "min_length" in msg.lower():
            min_length = error.get("ctx", {}).get("min_length", "指定された")
            messages.append(f"{field_jp}は{min_length}文字以上である必要があります")
        elif "string_too_long" in error_type or "max_length" in msg.lower():
            max_length = error.get("ctx", {}).get("max_length", "指定された")
            messages.append(f"{field_jp}は{max_length}文字以内である必要があります")
        elif "value_error" in error_type or msg:
            # 既に日本語のエラーメッセージの場合はそのまま使用
            if any(c in msg for c in "ひらがなカタカナ漢字"):
                messages.append(f"{field_jp}: {msg}")
            else:
                messages.append(f"{field_jp}の値が不正です: {msg}")
        else:
            messages.append(f"{field_jp}の入力に問題があります")
    
    return "、".join(messages) if messages else "入力値に問題があります"


def translate_exception_message(exception: Exception) -> str:
    """
    例外メッセージを日本語に変換
    
    引数:
        exception: 例外オブジェクト
    戻り値:
        str: 日本語化されたエラーメッセージ
    """
    error_str = str(exception)
    
    # 既に日本語の場合はそのまま返す
    if any(c in error_str for c in "ひらがなカタカナ漢字"):
        return error_str
    
    # 英語メッセージの日本語化マッピング
    translations = {
        "not found": "が見つかりません",
        "already exists": "は既に存在します",
        "invalid": "が無効です",
        "required": "が必要です",
        "failed": "に失敗しました",
        "error": "エラーが発生しました",
        "constraint": "制約違反",
        "null value": "空の値",
        "violates not-null constraint": "空の値を設定できません",
        "does not exist": "が存在しません",
        "duplicate": "重複",
        "unauthorized": "認証が必要です",
        "forbidden": "権限がありません",
        "integrity error": "データ整合性エラー",
        "programming error": "データベースエラー",
    }
    
    # 既知のエラーパターンにマッチするか確認
    for english, japanese in translations.items():
        if english.lower() in error_str.lower():
            return f"エラー: {japanese}"
    
    # マッチしない場合は一般的なメッセージを返す
    return f"エラーが発生しました: {error_str}"


@router.get("/providers", response_model=ProviderModelListResponse)
async def get_providers_and_models():
    """
    利用可能なプロバイダーとモデル一覧を取得
    
    戻り値:
        ProviderModelListResponse: プロバイダー・モデル一覧
    """
    try:
        providers = []
        for provider in ApiKeySettings.SUPPORTED_PROVIDERS:
            models = ApiKeySettings.get_supported_models(provider)
            providers.append(ProviderModelInfo(
                provider=provider,
                models=models
            ))
        
        return ProviderModelListResponse(providers=providers)
        
    except Exception as e:
        import traceback
        logger.error(f"プロバイダー一覧取得エラー: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プロバイダー一覧の取得に失敗しました"
        )


@router.post("/", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー登録
    
    テナント管理者がLLMプロバイダーのAPIキーを登録します。
    
    引数:
        api_key_data: APIキー作成データ
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyResponse: 作成されたAPIキー情報
    """
    try:
        logger.info(f"APIキー作成リクエスト: provider={api_key_data.provider}, model={api_key_data.model}, api_key_length={len(api_key_data.api_key)}")
        
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_key = await api_key_service.create_api_key(str(current_user.tenant_id), api_key_data)
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "create_api_key",
            "api_key",
            tenant_id=str(current_user.tenant_id),
            request=request,
            resource_id=str(api_key.id)
        )
        
        return ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            provider=api_key.provider,
            api_key_masked=ApiKeyResponse.mask_api_key(api_key_data.api_key),
            model=api_key.model,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )
        
    except RequestValidationError as e:
        logger.warning(f"APIキー作成Pydanticバリデーションエラー: {e.errors()}")
        # Pydanticのバリデーションエラーを日本語化して返す
        japanese_message = translate_validation_error(e.errors())
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=japanese_message
        )
    except (ValidationError, BusinessLogicError) as e:
        logger.warning(f"APIキー作成バリデーションエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"APIキー作成エラー: {str(e)}\n{traceback.format_exc()}")
        # エラーメッセージを日本語化
        japanese_message = translate_exception_message(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"APIキーの作成に失敗しました。{japanese_message}"
        )


@router.get("/", response_model=ApiKeyListResponse)
async def get_api_keys(
    current_user: User = Depends(require_tenant_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー一覧取得
    
    テナントのAPIキー一覧を取得します。
    テナント所属全ユーザー（運用者・監査者含む）がアクセス可能です。
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        # model/model_nameカラムの存在をチェック
        check_columns_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'api_keys' 
            AND column_name IN ('model', 'model_name')
        """)
        columns_check = await db.execute(check_columns_query)
        existing_columns = {row[0] for row in columns_check.fetchall()}
        has_model = 'model' in existing_columns
        has_model_name = 'model_name' in existing_columns
        
        # カラムに応じてSELECT文を構築
        if has_model and has_model_name:
            # 両方のカラムが存在する場合、modelを優先
            select_query = text("""
                SELECT id, tenant_id, provider, api_key, model, is_active, created_at, updated_at
                FROM api_keys
                WHERE tenant_id = :tid
                ORDER BY created_at DESC
            """)
        elif has_model:
            # modelのみ存在する場合
            select_query = text("""
                SELECT id, tenant_id, provider, api_key, model, is_active, created_at, updated_at
                FROM api_keys
                WHERE tenant_id = :tid
                ORDER BY created_at DESC
            """)
        elif has_model_name:
            # model_nameのみ存在する場合
            select_query = text("""
                SELECT id, tenant_id, provider, api_key, model_name, is_active, created_at, updated_at
                FROM api_keys
                WHERE tenant_id = :tid
                ORDER BY created_at DESC
            """)
        else:
            # どちらも存在しない場合
            select_query = text("""
            SELECT id, tenant_id, provider, api_key, is_active, created_at, updated_at
            FROM api_keys
            WHERE tenant_id = :tid
            ORDER BY created_at DESC
            """)
        
        result = await db.execute(select_query, {"tid": str(current_user.tenant_id)})
        rows = result.mappings().all()
        
        api_key_responses = []
        for r in rows:
            enc = r["api_key"]
            masked = ApiKeyResponse.mask_api_key(enc if isinstance(enc, str) else str(enc or ''))
            
            # モデル値の取得（modelを優先、なければmodel_name、なければ空文字列）
            model_value = ""
            if 'model' in r:
                model_value = r['model'] or ""
            elif 'model_name' in r:
                model_value = r['model_name'] or ""
            
            api_key_responses.append(ApiKeyResponse(
                id=str(r["id"]),
                tenant_id=str(r["tenant_id"]),
                provider=r["provider"],
                api_key_masked=masked,
                model=model_value,
                is_active=bool(r["is_active"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        
        return ApiKeyListResponse(
            api_keys=api_key_responses,
            total_count=len(api_key_responses)
        )
    except Exception as e:
        logger.error(f"APIキー一覧取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキー一覧の取得に失敗しました"
        )


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: str,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー詳細取得
    
    指定されたAPIキーの詳細情報を取得します。
    
    引数:
        api_key_id: APIキーID
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyResponse: APIキー詳細情報
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_key = await api_key_service.get_api_key(api_key_id, str(current_user.tenant_id))
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="APIキーが見つかりません"
            )
        
        # マスクされたAPIキーを生成
        decrypted_key = api_key_service.get_decrypted_api_key(api_key)
        masked_key = ApiKeyResponse.mask_api_key(decrypted_key)
        
        # modelカラムの存在をチェック
        check_columns_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'api_keys' 
            AND column_name IN ('model', 'model_name')
        """)
        columns_check = await db.execute(check_columns_query)
        existing_columns = {row[0] for row in columns_check.fetchall()}
        has_model = 'model' in existing_columns
        has_model_name = 'model_name' in existing_columns
        
        # model値の取得（modelを優先、なければmodel_name、なければ空文字列）
        model_value = ""
        if has_model:
            model_value = getattr(api_key, 'model', '') or ''
        elif has_model_name:
            model_value = getattr(api_key, 'model_name', '') or ''
        
        return ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            provider=api_key.provider,
            api_key_masked=masked_key,
            model=model_value,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"APIキー詳細取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキー詳細の取得に失敗しました"
        )


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: str,
    update_data: ApiKeyUpdate,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー更新
    
    指定されたAPIキーの情報を更新します。
    
    引数:
        api_key_id: APIキーID
        update_data: 更新データ
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        ApiKeyResponse: 更新されたAPIキー情報
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        api_key = await api_key_service.update_api_key(
            api_key_id, 
            str(current_user.tenant_id), 
            update_data
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="APIキーが見つかりません"
            )
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "update_api_key",
            "api_key",
            tenant_id=str(current_user.tenant_id),
            request=request,
            resource_id=api_key_id
        )
        
        # マスクされたAPIキーを生成
        decrypted_key = api_key_service.get_decrypted_api_key(api_key)
        masked_key = ApiKeyResponse.mask_api_key(decrypted_key)
        
        # modelカラムの存在をチェック
        check_columns_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'api_keys' 
            AND column_name IN ('model', 'model_name')
        """)
        columns_check = await db.execute(check_columns_query)
        existing_columns = {row[0] for row in columns_check.fetchall()}
        has_model = 'model' in existing_columns
        has_model_name = 'model_name' in existing_columns
        
        # model値の取得（modelを優先、なければmodel_name、なければ空文字列）
        model_value = ""
        if has_model:
            model_value = getattr(api_key, 'model', '') or ''
        elif has_model_name:
            model_value = getattr(api_key, 'model_name', '') or ''
        
        return ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            provider=api_key.provider,
            api_key_masked=masked_key,
            model=model_value,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )
        
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"APIキー更新エラー: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキーの更新に失敗しました"
        )


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    request: Request,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー削除
    
    指定されたAPIキーを削除します。
    
    引数:
        api_key_id: APIキーID
        current_user: 認証済みユーザー（テナント管理者）
        db: データベースセッション
        
    戻り値:
        dict: 削除完了メッセージ
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        api_key_service = ApiKeyService(db)
        success = await api_key_service.delete_api_key(api_key_id, str(current_user.tenant_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="APIキーが見つかりません"
            )
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "delete_api_key",
            "api_key",
            tenant_id=str(current_user.tenant_id),
            request=request,
            resource_id=api_key_id
        )
        
        return {"message": "APIキーが削除されました"}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"APIキー削除エラー: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APIキーの削除に失敗しました"
        )


class InlineVerifyRequest(BaseModel):
    provider: str
    model: str | None = None
    api_key: str


@router.post("/verify-inline")
async def verify_api_key_inline(
    payload: InlineVerifyRequest,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー検証（登録前）
    
    登録フォームから受け取った provider/model/api_key を用いて有効性を軽量検証します。
    管理者権限が必要です。
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        service = ApiKeyService(db)
        result = await service.verify_api_key(payload.provider, payload.api_key, payload.model or "")
        BusinessLogger.log_user_action(
            str(current_user.id),
            "verify_api_key_inline",
            "api_key",
            tenant_id=str(current_user.tenant_id)
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.exception(e, {"operation": "verify_api_key_inline"})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="APIキー検証に失敗しました")


@router.post("/{api_key_id}/verify")
async def verify_api_key(
    api_key_id: str,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """
    APIキー検証
    
    指定されたAPIキーが有効に利用可能かを軽量に検証します。
    管理者権限が必要です。
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        tenant_id = str(current_user.tenant_id)

        service = ApiKeyService(db)
        api_key = await service.get_api_key(api_key_id, tenant_id)
        if not api_key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="APIキーが見つかりません")

        decrypted = service.get_decrypted_api_key(api_key)
        model_value = getattr(api_key, 'model', '') or getattr(api_key, 'model_name', '') or ''
        result = await service.verify_api_key(api_key.provider, decrypted, model_value)

        BusinessLogger.log_user_action(
            str(current_user.id),
            "verify_api_key",
            "api_key",
            tenant_id=tenant_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.exception(e, {"operation": "verify_api_key"})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="APIキー検証に失敗しました")
