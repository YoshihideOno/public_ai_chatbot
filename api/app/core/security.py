"""
セキュリティ機能

このファイルはアプリケーションのセキュリティ関連機能を実装します。
パスワードハッシュ化、JWTトークンの生成・検証、認証・認可の基盤となる
機能を提供します。

主な機能:
- パスワードのハッシュ化・検証
- JWTアクセストークンの生成・検証
- JWTリフレッシュトークンの生成・検証
- トークンからのユーザー情報抽出
- トークンの有効期限チェック
"""

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.exceptions import AuthenticationError, InvalidTokenError, TokenExpiredError
from app.utils.logging import SecurityLogger, ErrorLogger, logger

# パスワードハッシュ化コンテキスト
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワードの検証
    
    平文パスワードとハッシュ化されたパスワードを比較して検証します。
    bcryptアルゴリズムを使用してセキュアな検証を行います。
    
    引数:
        plain_password: 平文パスワード
        hashed_password: ハッシュ化されたパスワード
        
    戻り値:
        bool: パスワードが一致する場合True、そうでなければFalse
        
    例外:
        ValueError: 無効なパスワード形式
    """
    try:
        if not plain_password or not hashed_password:
            logger.warning("空のパスワードまたはハッシュが提供されました")
            return False
            
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"パスワード検証結果: {'成功' if result else '失敗'}")
        return result
    except Exception as e:
        ErrorLogger.log_exception(e, {"operation": "verify_password"})
        raise ValueError("パスワード検証中にエラーが発生しました")


def get_password_hash(password: str) -> str:
    """
    パスワードのハッシュ化
    
    平文パスワードをbcryptアルゴリズムでハッシュ化します。
    セキュリティのため、ソルトを自動生成してハッシュ化します。
    
    引数:
        password: 平文パスワード
        
    戻り値:
        str: ハッシュ化されたパスワード
        
    例外:
        ValueError: 無効なパスワード
    """
    try:
        if not password:
            raise ValueError("パスワードが空です")
            
        if len(password) < 8:
            raise ValueError("パスワードは8文字以上である必要があります")
            
        hashed = pwd_context.hash(password)
        logger.info("パスワードのハッシュ化が完了しました")
        return hashed
    except Exception as e:
        ErrorLogger.log_exception(e, {"operation": "get_password_hash"})
        raise ValueError("パスワードのハッシュ化に失敗しました")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンの生成
    
    ユーザー情報を含むJWTアクセストークンを生成します。
    デフォルトの有効期限は設定ファイルから取得します。
    
    引数:
        data: トークンに含めるユーザーデータ
        expires_delta: カスタム有効期限（オプション）
        
    戻り値:
        str: エンコードされたJWTトークン
        
    例外:
        ValueError: 無効なデータまたは設定
    """
    try:
        if not data or "sub" not in data:
            raise ValueError("ユーザーID（sub）が必須です")
            
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        import time
        now = datetime.utcnow()
        to_encode.update({
            "exp": expire, 
            "iat": now,
            "jti": f"{data.get('sub', '')}-{time.time_ns()}",  # 一意性を保証するためのJWT ID
        })
        # typeが既に設定されている場合は上書きしない
        if "type" not in to_encode:
            to_encode["type"] = "access"
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.info(f"アクセストークン生成完了: ユーザーID {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        ErrorLogger.log_exception(e, {"operation": "create_access_token"})
        raise ValueError("アクセストークンの生成に失敗しました")


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTリフレッシュトークンの生成
    
    アクセストークンの更新に使用するJWTリフレッシュトークンを生成します。
    アクセストークンより長い有効期限を持ちます。
    
    引数:
        data: トークンに含めるユーザーデータ
        expires_delta: カスタム有効期限（オプション）
        
    戻り値:
        str: エンコードされたJWTリフレッシュトークン
        
    例外:
        ValueError: 無効なデータまたは設定
    """
    try:
        if not data or "sub" not in data:
            raise ValueError("ユーザーID（sub）が必須です")
            
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        import time
        now = datetime.utcnow()
        to_encode.update({
            "exp": expire, 
            "iat": now, 
            "type": "refresh",
            "jti": f"{data.get('sub', '')}-{time.time_ns()}",  # 一意性を保証するためのJWT ID
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.info(f"リフレッシュトークン生成完了: ユーザーID {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        ErrorLogger.log_exception(e, {"operation": "create_refresh_token"})
        raise ValueError("リフレッシュトークンの生成に失敗しました")


def verify_token(token: str) -> Dict[str, Any]:
    """
    JWTトークンの検証・デコード
    
    JWTトークンの署名と有効期限を検証し、ペイロードをデコードします。
    無効なトークンの場合は適切な例外を発生させます。
    
    引数:
        token: 検証するJWTトークン
        
    戻り値:
        Dict[str, Any]: デコードされたトークンペイロード
        
    例外:
        InvalidTokenError: 無効なトークン
        TokenExpiredError: 期限切れトークン
    """
    try:
        if not token:
            raise InvalidTokenError()
            
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # トークンタイプの検証
        token_type = payload.get("type")
        if token_type not in ["access", "refresh", "password_reset"]:
            logger.warning(f"無効なトークンタイプ: {token_type}")
            raise InvalidTokenError()
            
        logger.info(f"トークン検証成功: タイプ {token_type}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("期限切れトークンが検出されました")
        raise TokenExpiredError()
    except JWTError as e:
        logger.warning(f"無効なトークン: {str(e)}")
        raise InvalidTokenError()


def extract_user_id_from_token(token: str) -> Optional[int]:
    """
    トークンからユーザーIDを抽出
    
    JWTトークンを検証し、ペイロードからユーザーIDを抽出します。
    トークンが無効な場合はNoneを返します。
    
    引数:
        token: JWTトークン
        
    戻り値:
        Optional[int]: ユーザーID、無効な場合はNone
        
    例外:
        なし（エラー時はNoneを返す）
    """
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            logger.warning("トークンにユーザーIDが含まれていません")
            return None
            
        user_id_int = int(user_id)
        logger.info(f"ユーザーID抽出成功: {user_id_int}")
        return user_id_int
    except (InvalidTokenError, TokenExpiredError, ValueError) as e:
        logger.warning(f"ユーザーID抽出失敗: {str(e)}")
        return None


def is_token_expired(token: str) -> bool:
    """
    トークンの有効期限チェック
    
    トークンの有効期限をチェックし、期限切れかどうかを判定します。
    署名検証は行わず、有効期限のみをチェックします。
    
    引数:
        token: チェックするJWTトークン
        
    戻り値:
        bool: 期限切れの場合True、有効な場合False
        
    例外:
        なし（エラー時はTrueを返す）
    """
    try:
        if not token:
            return True
            
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM], 
            options={"verify_exp": False}
        )
        
        exp = payload.get("exp")
        if exp is None:
            logger.warning("トークンに有効期限が設定されていません")
            return True
            
        is_expired = datetime.utcnow().timestamp() > exp
        logger.info(f"トークン有効期限チェック: {'期限切れ' if is_expired else '有効'}")
        return is_expired
    except JWTError as e:
        logger.warning(f"トークン有効期限チェックエラー: {str(e)}")
        return True
