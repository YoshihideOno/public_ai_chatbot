"""
APIキー管理サービス

このファイルはAPIキーに関するビジネスロジックを実装します。
APIキーのCRUD操作、暗号化・復号化、バリデーションなどの機能を提供します。

主な機能:
- APIキーの作成・更新・削除
- APIキーの暗号化・復号化
- プロバイダー・モデル検証
- テナント毎のAPIキー管理
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse
from app.core.exceptions import (
    ApiKeyNotFoundError, ValidationError, BusinessLogicError
)
from app.utils.logging import SecurityLogger, BusinessLogger, ErrorLogger, logger
from app.core.config import settings
import base64
from typing import Dict, Any
from app.utils.common import RetryUtils

try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None  # type: ignore

# Google Generative AI SDK（同期APIのため to_thread で実行）
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

# Anthropic SDK（非同期）
try:
    from anthropic import AsyncAnthropic  # type: ignore
    import httpx  # type: ignore
except Exception:
    AsyncAnthropic = None  # type: ignore
    httpx = None  # type: ignore


class ApiKeyService:
    """
    APIキー管理サービス
    
    APIキーに関する全てのビジネスロジックを担当します。
    データベース操作、暗号化、バリデーション、セキュリティチェックなどを統合的に管理します。
    
    属性:
        db: データベースセッション（AsyncSession）
        cipher: 暗号化オブジェクト（Fernet）
    """
    
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        引数:
            db: データベースセッション
        """
        self.db = db
        # 暗号化キーの生成（本番環境では環境変数から取得）
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        self.cipher = Fernet(base64.urlsafe_b64encode(key))

    @RetryUtils.retry_on_exception(max_retries=1, delay=1.0)
    async def verify_api_key(self, provider: str, api_key: str, model: str) -> Dict[str, Any]:
        """
        APIキーの有効性を軽量に検証する
        
        引数:
            provider: プロバイダー名（openai など）
            api_key: 平文APIキー
            model: 検証対象モデル
        戻り値:
            { valid: bool, provider: str, model: str, message?: str, error_code?: str }
        """
        try:
            provider_l = provider.lower()
            if provider_l == "openai":
                if AsyncOpenAI is None:
                    return {"valid": False, "provider": provider, "model": model, "error_code": "sdk_unavailable", "message": "OpenAI SDKが利用できません"}
                client = AsyncOpenAI(api_key=api_key, timeout=10.0)
                # Embeddings API で短文をテスト
                test_model = model
                # モデルがチャットモデルの場合でも通るよう、embedding系モデルにフォールバック（軽いマッピング）
                if not test_model or "embedding" not in test_model:
                    test_model = "text-embedding-3-small"
                await client.embeddings.create(model=test_model, input="ping")
                return {"valid": True, "provider": provider, "model": test_model, "message": "OK"}
            elif provider_l == "google":
                if genai is None:
                    return {"valid": False, "provider": provider, "model": model, "error_code": "sdk_unavailable", "message": "Google Generative AI SDKが利用できません"}
                # 同期APIをスレッドで実行
                import asyncio
                genai.configure(api_key=api_key)

                # 優先候補（SDKの世代に合わせて順序付け）
                candidate_models = []
                if model:
                    candidate_models.append(model)
                candidate_models += [
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-pro-latest",
                    "gemini-1.5-flash",
                    "gemini-1.5-pro",
                    "gemini-pro",
                ]

                last_err: Exception | None = None

                def _try_generate(mname: str):
                    gm = genai.GenerativeModel(mname)
                    return gm.generate_content("ping")

                # 404やメソッド非対応は次候補へフォールバック
                for mname in candidate_models:
                    try:
                        await asyncio.to_thread(_try_generate, mname)
                        return {"valid": True, "provider": provider, "model": mname, "message": "OK"}
                    except Exception as e:  # noqa: BLE001
                        msg = str(e).lower()
                        last_err = e
                        if "not found" in msg or "not supported" in msg or "404" in msg:
                            continue
                        # その他は即時エラー
                        raise

                # モデル一覧から generateContent 対応を探索
                try:
                    def _list_models():
                        return list(genai.list_models())
                    models = await asyncio.to_thread(_list_models)
                    # プロパティ名はSDKにより差異がある可能性があるため両対応
                    def _supports_generate_content(md) -> bool:
                        methods = getattr(md, "supported_generation_methods", None) or getattr(md, "generation_methods", None) or []
                        return "generateContent" in methods or "generate_content" in methods
                    for md in models:
                        if _supports_generate_content(md):
                            try:
                                await asyncio.to_thread(_try_generate, getattr(md, "name", str(md)))
                                return {"valid": True, "provider": provider, "model": getattr(md, "name", "unknown"), "message": "OK"}
                            except Exception:  # noqa: BLE001
                                continue
                except Exception:
                    # 無視して最後のエラーを返却
                    pass

                # ここまで失敗
                msg = str(last_err) if last_err else "対応するモデルが見つかりません"
                return {"valid": False, "provider": provider, "model": model, "error_code": "model_not_found", "message": msg}
            elif provider_l == "anthropic":
                if AsyncAnthropic is None or httpx is None:
                    return {"valid": False, "provider": provider, "model": model, "error_code": "sdk_unavailable", "message": "Anthropic SDKが利用できません"}
                # httpxクライアントを明示的に作成してproxiesを除外
                http_client = httpx.AsyncClient(timeout=10.0)
                client = AsyncAnthropic(api_key=api_key, http_client=http_client)
                try:
                    # モデル名のエイリアスを解決（Anthropicは日付付モデルIDや -latest を要求）
                    alias_map = {
                        # Claude 3.5 系
                        "claude-3-5-sonnet": "claude-3-5-sonnet-latest",
                        "claude-3-5-haiku": "claude-3-5-haiku-latest",
                        # Claude 3 系（2024日付版）
                        "claude-3-opus": "claude-3-opus-20240229",
                        "claude-3-sonnet": "claude-3-sonnet-20240229",
                        "claude-3-haiku": "claude-3-haiku-20240307",
                    }
                    raw_model = (model or "claude-3-haiku-20240307").strip()
                    key = raw_model.lower()
                    test_model = alias_map.get(key, raw_model)
                    try:
                        await client.messages.create(
                            model=test_model,
                            max_tokens=1,
                            messages=[{"role": "user", "content": "ping"}],
                        )
                        return {"valid": True, "provider": provider, "model": test_model, "message": "OK"}
                    except Exception as e:  # noqa: BLE001
                        # 404/モデル未提供時はフォールバック候補で再試行
                        ml = str(e).lower()
                        if ("not_found" in ml or "not found" in ml or "404" in ml) and ("model" in ml or "claude" in ml):
                            fallback_candidates = [
                                # できれば3.5系を優先
                                "claude-3-5-sonnet-latest",
                                "claude-3-5-haiku-latest",
                                # 安定の3系
                                "claude-3-haiku-20240307",
                                "claude-3-sonnet-20240229",
                            ]
                            for cand in fallback_candidates:
                                try:
                                    await client.messages.create(
                                        model=cand,
                                        max_tokens=1,
                                        messages=[{"role": "user", "content": "ping"}],
                                    )
                                    return {"valid": True, "provider": provider, "model": cand, "message": "OK (fallback)"}
                                except Exception:  # noqa: BLE001
                                    continue
                            # フォールバック全滅なら元の例外を投げ直し → 上位で分類
                            raise
                        # その他のエラーはそのまま上位で分類
                        raise
                finally:
                    await http_client.aclose()
            else:
                return {"valid": False, "provider": provider, "model": model, "error_code": "unsupported_provider", "message": "未サポートのプロバイダーです"}
        except Exception as e:
            # 代表的なエラーの文言を簡易マッピング
            msg = str(e)
            code = "unknown_error"
            ml = msg.lower()
            
            # 残高不足エラーの検出（優先度: 高）
            if "credit balance" in ml or "credit" in ml and ("too low" in ml or "insufficient" in ml):
                code = "insufficient_credits"
                # エラーメッセージから詳細を抽出
                if "Your credit balance is too low" in msg:
                    user_msg = "Anthropic APIの残高が不足しています。Plans & Billingでクレジットを追加してください。"
                else:
                    user_msg = "APIキーの残高が不足しています。"
            elif "unauthorized" in ml or ("authentication" in ml and "failed" in ml):
                code = "unauthorized"
                user_msg = "APIキーが無効または認証に失敗しました。"
            elif "rate" in ml and "limit" in ml:
                code = "rate_limited"
                user_msg = "レート制限に達しました。しばらく待ってから再試行してください。"
            elif "timeout" in ml:
                code = "timeout"
                user_msg = "リクエストがタイムアウトしました。"
            elif "invalid" in ml and "request" in ml:
                code = "invalid_request"
                user_msg = "無効なリクエストです。"
            elif ("not_found" in ml or "not found" in ml or "404" in ml) and ("model" in ml or "claude" in ml):
                code = "model_not_found"
                user_msg = (
                    "指定のAnthropicモデルが見つかりません。例: 'claude-3-5-sonnet-latest' や "
                    "'claude-3-haiku-20240307' を使用してください。"
                )
            else:
                user_msg = msg
            
            logger.error(f"APIキー検証エラー: provider={provider}, model={model}, error={msg}")
            return {"valid": False, "provider": provider, "model": model, "error_code": code, "message": user_msg}
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """
        APIキーを暗号化
        
        引数:
            api_key: 平文のAPIキー
        戻り値:
            str: 暗号化されたAPIキー
        """
        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"APIキー暗号化エラー: {str(e)}")
            raise BusinessLogicError("APIキーの暗号化に失敗しました")
    
    def _decrypt_api_key(self, encrypted_api_key: str) -> str:
        """
        APIキーを復号化
        
        引数:
            encrypted_api_key: 暗号化されたAPIキー
        戻り値:
            str: 平文のAPIキー
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_api_key.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"APIキー復号化エラー: {str(e)}")
            raise BusinessLogicError("APIキーの復号化に失敗しました")
    
    async def create_api_key(self, tenant_id: str, api_key_data: ApiKeyCreate) -> ApiKey:
        """
        APIキー作成
        
        引数:
            tenant_id: テナントID
            api_key_data: APIキー作成データ
        戻り値:
            ApiKey: 作成されたAPIキー
        """
        try:
            # 既存のAPIキーをチェック（同じプロバイダー + 同じモデル + is_active = true）
            # model/model_nameカラムが存在しない可能性があるため、まずカラムの存在をチェック
            check_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'api_keys' 
                AND column_name IN ('model', 'model_name')
            """)
            columns_check = await self.db.execute(check_columns_query)
            existing_columns = {row[0] for row in columns_check.fetchall()}
            has_model = 'model' in existing_columns
            has_model_name = 'model_name' in existing_columns
            
            # カラムに応じて重複チェッククエリを構築
            if has_model and has_model_name:
                # 両方のカラムが存在する場合、modelを優先
                existing_query = text("""
                    SELECT id FROM api_keys 
                    WHERE tenant_id = :tid 
                    AND provider = :provider 
                    AND model = :model
                    AND is_active = true
                    LIMIT 1
                """)
                params = {"tid": tenant_id, "provider": api_key_data.provider, "model": api_key_data.model}
            elif has_model:
                # modelのみ存在する場合
                existing_query = text("""
                    SELECT id FROM api_keys 
                    WHERE tenant_id = :tid 
                    AND provider = :provider 
                    AND model = :model
                    AND is_active = true
                    LIMIT 1
                """)
                params = {"tid": tenant_id, "provider": api_key_data.provider, "model": api_key_data.model}
            elif has_model_name:
                # model_nameのみ存在する場合
                existing_query = text("""
                    SELECT id FROM api_keys 
                    WHERE tenant_id = :tid 
                    AND provider = :provider 
                    AND model_name = :model
                    AND is_active = true
                    LIMIT 1
                """)
                params = {"tid": tenant_id, "provider": api_key_data.provider, "model": api_key_data.model}
            else:
                # どちらも存在しない場合、プロバイダーのみでチェック
                existing_query = text("""
                    SELECT id FROM api_keys 
                    WHERE tenant_id = :tid 
                    AND provider = :provider 
                    AND is_active = true
                    LIMIT 1
                """)
                params = {"tid": tenant_id, "provider": api_key_data.provider}
            
            result = await self.db.execute(existing_query, params)
            existing_row = result.first()
            
            if existing_row:
                raise BusinessLogicError(f"プロバイダー {api_key_data.provider} のモデル {api_key_data.model} のAPIキーは既に登録されています")
            
            # APIキーを暗号化
            encrypted_api_key = self._encrypt_api_key(api_key_data.api_key)
            
            # APIキー作成
            # model/model_nameカラムが存在しない可能性があるため、まずカラムの存在をチェック
            check_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'api_keys' 
                AND column_name IN ('model', 'model_name')
            """)
            columns_check = await self.db.execute(check_columns_query)
            existing_columns = {row[0] for row in columns_check.fetchall()}
            has_model = 'model' in existing_columns
            has_model_name = 'model_name' in existing_columns
            
            # カラムに応じてINSERT文を構築
            if has_model and has_model_name:
                # 両方のカラムが存在する場合
                insert_query = text("""
                    INSERT INTO api_keys (tenant_id, provider, api_key, model, model_name, is_active, created_at, updated_at)
                    VALUES (:tid, :provider, :api_key, :model, :model, true, NOW(), NOW())
                    RETURNING id, tenant_id, provider, api_key, model, model_name, is_active, created_at, updated_at
                """)
                params = {
                    "tid": tenant_id,
                    "provider": api_key_data.provider,
                    "api_key": encrypted_api_key,
                    "model": api_key_data.model
                }
            elif has_model:
                # modelのみ存在する場合
                insert_query = text("""
                    INSERT INTO api_keys (tenant_id, provider, api_key, model, is_active, created_at, updated_at)
                    VALUES (:tid, :provider, :api_key, :model, true, NOW(), NOW())
                    RETURNING id, tenant_id, provider, api_key, model, is_active, created_at, updated_at
                """)
                params = {
                    "tid": tenant_id,
                    "provider": api_key_data.provider,
                    "api_key": encrypted_api_key,
                    "model": api_key_data.model
                }
            elif has_model_name:
                # model_nameのみ存在する場合
                insert_query = text("""
                    INSERT INTO api_keys (tenant_id, provider, api_key, model_name, is_active, created_at, updated_at)
                    VALUES (:tid, :provider, :api_key, :model_name, true, NOW(), NOW())
                    RETURNING id, tenant_id, provider, api_key, model_name, is_active, created_at, updated_at
                """)
                params = {
                    "tid": tenant_id,
                    "provider": api_key_data.provider,
                    "api_key": encrypted_api_key,
                    "model_name": api_key_data.model
                }
            else:
                # どちらも存在しない場合
                insert_query = text("""
                    INSERT INTO api_keys (tenant_id, provider, api_key, is_active, created_at, updated_at)
                    VALUES (:tid, :provider, :api_key, true, NOW(), NOW())
                    RETURNING id, tenant_id, provider, api_key, is_active, created_at, updated_at
                """)
                params = {
                    "tid": tenant_id,
                    "provider": api_key_data.provider,
                    "api_key": encrypted_api_key
                }
            
            result = await self.db.execute(insert_query, params)
            
            row_mapping = result.mappings().first()
            
            # 結果からApiKeyオブジェクトを作成
            if not row_mapping:
                raise BusinessLogicError("APIキーの作成に失敗しました")
            
            # model値の取得（model_nameが存在する場合はそれを使用、なければmodel、なければapi_key_data.model）
            model_value = None
            if 'model' in row_mapping:
                model_value = row_mapping['model']
            elif 'model_name' in row_mapping:
                model_value = row_mapping['model_name']
            else:
                model_value = api_key_data.model  # メモリ上のみ保持
            
            db_api_key = ApiKey(
                id=row_mapping['id'],
                tenant_id=row_mapping['tenant_id'],
                provider=row_mapping['provider'],
                api_key=row_mapping['api_key'],
                model_name=model_value,
                is_active=row_mapping['is_active'],
                created_at=row_mapping['created_at'],
                updated_at=row_mapping['updated_at']
            )
            
            await self.db.commit()
            
            BusinessLogger.log_tenant_action(
                tenant_id,
                "create_api_key",
                {"provider": api_key_data.provider, "model": api_key_data.model}
            )
            
            logger.info(f"APIキー作成完了: tenant={tenant_id}, provider={api_key_data.provider}")
            return db_api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"APIキー作成エラー: {str(e)}")
            raise
    
    async def get_api_key(self, api_key_id: str, tenant_id: str) -> Optional[ApiKey]:
        """
        APIキー取得
        
        引数:
            api_key_id: APIキーID
            tenant_id: テナントID
        戻り値:
            Optional[ApiKey]: APIキー情報（存在しない場合はNone）
        """
        try:
            # model/model_nameカラムの存在をチェック
            check_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'api_keys' 
                AND column_name IN ('model', 'model_name')
            """)
            columns_check = await self.db.execute(check_columns_query)
            existing_columns = {row[0] for row in columns_check.fetchall()}
            has_model = 'model' in existing_columns
            has_model_name = 'model_name' in existing_columns
            
            # カラムに応じてSELECT文を構築
            if has_model and has_model_name:
                # 両方のカラムが存在する場合、modelを優先
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, model, model_name, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE id = :api_key_id AND tenant_id = :tid
                """)
            elif has_model:
                # modelのみ存在する場合
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, model, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE id = :api_key_id AND tenant_id = :tid
                """)
            elif has_model_name:
                # model_nameのみ存在する場合
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, model_name, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE id = :api_key_id AND tenant_id = :tid
                """)
            else:
                # どちらも存在しない場合
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE id = :api_key_id AND tenant_id = :tid
                """)
            
            result = await self.db.execute(
                select_query,
                {"api_key_id": api_key_id, "tid": tenant_id}
            )
            row = result.mappings().first()
            
            if not row:
                return None
            
            # ApiKeyオブジェクトを構築
            # モデル値の取得（modelを優先、なければmodel_name、なければ空文字列）
            model_value = ""
            if 'model' in row:
                model_value = row['model'] or ""
            elif 'model_name' in row:
                model_value = row['model_name'] or ""
            
            # ApiKeyオブジェクトを作成
            api_key = ApiKey(
                id=row['id'],
                tenant_id=row['tenant_id'],
                provider=row['provider'],
                api_key=row['api_key'],
                model_name=model_value,  # カラムが存在しない場合は空文字列
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
            return api_key
            
        except Exception as e:
            logger.error(f"APIキー取得エラー: {str(e)}")
            raise
    
    async def get_api_keys_by_tenant(self, tenant_id: str) -> List[ApiKey]:
        """
        テナントのAPIキー一覧取得
        
        引数:
            tenant_id: テナントID
        戻り値:
            List[ApiKey]: APIキー一覧
        """
        from sqlalchemy.exc import ProgrammingError
        try:
            query = select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at.desc())
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except ProgrammingError as pe:
            # ProgrammingErrorはそのまま再レイズ（エンドポイントで処理）
            raise pe
        except Exception as e:
            logger.error(f"APIキー一覧取得エラー: {str(e)}")
            raise
    
    async def update_api_key(self, api_key_id: str, tenant_id: str, update_data: ApiKeyUpdate) -> Optional[ApiKey]:
        """
        APIキー更新
        
        引数:
            api_key_id: APIキーID
            tenant_id: テナントID
            update_data: 更新データ
        戻り値:
            Optional[ApiKey]: 更新されたAPIキー（存在しない場合はNone）
        """
        try:
            # まずAPIキーの存在確認
            api_key = await self.get_api_key(api_key_id, tenant_id)
            if not api_key:
                return None
            
            # model/model_nameカラムの存在をチェック
            check_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'api_keys' 
                AND column_name IN ('model', 'model_name')
            """)
            columns_check = await self.db.execute(check_columns_query)
            existing_columns = {row[0] for row in columns_check.fetchall()}
            has_model = 'model' in existing_columns
            has_model_name = 'model_name' in existing_columns
            
            # 更新フィールドを構築
            update_fields = []
            params = {"api_key_id": api_key_id, "tid": tenant_id}
            
            if update_data.api_key is not None:
                encrypted_api_key = self._encrypt_api_key(update_data.api_key)
                update_fields.append("api_key = :api_key")
                params["api_key"] = encrypted_api_key
            
            if update_data.model is not None:
                if has_model:
                    update_fields.append("model = :model")
                    params["model"] = update_data.model
                elif has_model_name:
                    update_fields.append("model_name = :model")
                    params["model"] = update_data.model
                # どちらも存在しない場合は何もしない
            
            if update_data.is_active is not None:
                update_fields.append("is_active = :is_active")
                params["is_active"] = update_data.is_active
            
            # 更新フィールドがある場合のみUPDATEを実行
            if update_fields:
                update_fields.append("updated_at = NOW()")
                update_query = text(f"""
                    UPDATE api_keys 
                    SET {', '.join(update_fields)}
                    WHERE id = :api_key_id AND tenant_id = :tid
                """)
                await self.db.execute(update_query, params)
            await self.db.commit()
            
            # 更新後に再度取得して返す
            updated_api_key = await self.get_api_key(api_key_id, tenant_id)
            
            BusinessLogger.log_tenant_action(
                tenant_id,
                "update_api_key",
                {"api_key_id": api_key_id}
            )
            
            logger.info(f"APIキー更新完了: tenant={tenant_id}, api_key_id={api_key_id}")
            return updated_api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"APIキー更新エラー: {str(e)}")
            raise
    
    async def delete_api_key(self, api_key_id: str, tenant_id: str) -> bool:
        """
        APIキー削除
        
        引数:
            api_key_id: APIキーID
            tenant_id: テナントID
        戻り値:
            bool: 削除成功時True
        """
        try:
            # APIキー取得（存在確認用）
            api_key = await self.get_api_key(api_key_id, tenant_id)
            if not api_key:
                return False
            
            # 生SQLでDELETEを実行（get_api_keyで作成したオブジェクトはセッションに紐づいていないため）
            delete_query = text("""
                DELETE FROM api_keys
                WHERE id = :api_key_id AND tenant_id = :tid
            """)
            result = await self.db.execute(
                delete_query,
                {"api_key_id": api_key_id, "tid": tenant_id}
            )
            await self.db.commit()
            
            # 削除された行数が0の場合はFalseを返す
            if result.rowcount == 0:
                return False
            
            BusinessLogger.log_tenant_action(
                tenant_id,
                "delete_api_key",
                {"api_key_id": api_key_id, "provider": api_key.provider}
            )
            
            logger.info(f"APIキー削除完了: tenant={tenant_id}, api_key_id={api_key_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"APIキー削除エラー: {str(e)}")
            raise
    
    async def get_active_api_key_by_provider(self, tenant_id: str, provider: str) -> Optional[ApiKey]:
        """
        プロバイダー別のアクティブAPIキー取得
        
        引数:
            tenant_id: テナントID
            provider: プロバイダー名
        戻り値:
            Optional[ApiKey]: アクティブなAPIキー（存在しない場合はNone）
        """
        try:
            # model/model_nameカラムの存在をチェック
            check_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'api_keys' 
                AND column_name IN ('model', 'model_name')
            """)
            columns_check = await self.db.execute(check_columns_query)
            existing_columns = {row[0] for row in columns_check.fetchall()}
            has_model = 'model' in existing_columns
            has_model_name = 'model_name' in existing_columns
            
            # カラムに応じてSELECT文を構築
            if has_model and has_model_name:
                # 両方のカラムが存在する場合、modelを優先
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, model, model_name, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE tenant_id = :tid AND provider = :provider AND is_active = true
                    LIMIT 1
                """)
            elif has_model:
                # modelのみ存在する場合
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, model, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE tenant_id = :tid AND provider = :provider AND is_active = true
                    LIMIT 1
                """)
            elif has_model_name:
                # model_nameのみ存在する場合
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, model_name, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE tenant_id = :tid AND provider = :provider AND is_active = true
                    LIMIT 1
                """)
            else:
                # どちらも存在しない場合
                select_query = text("""
                    SELECT id, tenant_id, provider, api_key, is_active, created_at, updated_at
                    FROM api_keys
                    WHERE tenant_id = :tid AND provider = :provider AND is_active = true
                    LIMIT 1
                """)
            
            result = await self.db.execute(
                select_query,
                {"tid": tenant_id, "provider": provider}
            )
            row = result.mappings().first()
            
            if not row:
                return None
            
            # 結果をApiKeyオブジェクトに変換
            # カラム名の違いを吸収（model_name → model）
            api_key_dict = dict(row)
            if 'model_name' in api_key_dict and 'model' not in api_key_dict:
                api_key_dict['model'] = api_key_dict.pop('model_name')
            
            # ApiKeyオブジェクトを作成（モデルに存在しないカラムはNoneに設定）
            api_key_obj = ApiKey(
                id=api_key_dict['id'],
                tenant_id=api_key_dict['tenant_id'],
                provider=api_key_dict['provider'],
                api_key=api_key_dict['api_key'],
                model_name=api_key_dict.get('model_name', api_key_dict.get('model', '')),
                is_active=api_key_dict['is_active'],
                created_at=api_key_dict['created_at'],
                updated_at=api_key_dict['updated_at']
            )
            
            return api_key_obj
            
        except Exception as e:
            logger.error(f"プロバイダー別APIキー取得エラー: {str(e)}")
            raise
    
    def get_decrypted_api_key(self, api_key: ApiKey) -> str:
        """
        復号化されたAPIキーを取得
        
        引数:
            api_key: APIキーオブジェクト
        戻り値:
            str: 復号化されたAPIキー
        """
        return self._decrypt_api_key(api_key.api_key)
