"""
カスタム例外クラス定義

このファイルはアプリケーション全体で使用するカスタム例外クラスを定義します。
FastAPIのHTTPExceptionを拡張し、エラーコード、詳細情報、適切なHTTPステータスコードを
含む統一された例外処理を提供します。

主な機能:
- カスタムHTTP例外の定義
- 認証・認可エラーの定義
- バリデーションエラーの定義
- ビジネスロジックエラーの定義
- リソース関連エラーの定義
- レート制限エラーの定義
"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from app.utils.logging import BusinessLogger, SecurityLogger


class CustomHTTPException(HTTPException):
    """
    カスタムHTTP例外クラス
    
    FastAPIのHTTPExceptionを拡張し、エラーコードと詳細情報を追加します。
    統一されたエラーレスポンス形式を提供し、ログ出力とデバッグを容易にします。
    
    属性:
        status_code: HTTPステータスコード
        detail: エラーメッセージ
        error_code: アプリケーション固有のエラーコード
        error_details: エラーの詳細情報
        headers: HTTPヘッダー
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        カスタムHTTP例外の初期化
        
        引数:
            status_code: HTTPステータスコード
            detail: エラーメッセージ
            error_code: アプリケーション固有のエラーコード
            error_details: エラーの詳細情報
            headers: HTTPヘッダー
            
        例外:
            HTTPException: FastAPIのHTTP例外
        """
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.error_details = error_details
        
        # エラーログの出力
        BusinessLogger.error(f"HTTP例外発生: {error_code} - {detail}")


class AuthenticationError(CustomHTTPException):
    """
    認証エラークラス
    
    ユーザー認証に関するエラーを処理します。
    401 Unauthorizedステータスコードを返し、認証が必要であることを示します。
    """
    
    def __init__(self, detail: str = "認証に失敗しました"):
        """
        認証エラーの初期化
        
        引数:
            detail: エラーメッセージ
            
        戻り値:
            AuthenticationError: 認証エラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )
        SecurityLogger.warning(f"認証エラー: {detail}")


class AuthorizationError(CustomHTTPException):
    """
    認可エラークラス
    
    ユーザーの権限不足に関するエラーを処理します。
    403 Forbiddenステータスコードを返し、アクセス権限がないことを示します。
    """
    
    def __init__(self, detail: str = "権限が不足しています"):
        """
        認可エラーの初期化
        
        引数:
            detail: エラーメッセージ
            
        戻り値:
            AuthorizationError: 認可エラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR"
        )
        SecurityLogger.warning(f"認可エラー: {detail}")


class ValidationError(CustomHTTPException):
    """
    バリデーションエラークラス
    
    入力値の検証に関するエラーを処理します。
    422 Unprocessable Entityステータスコードを返し、入力値が無効であることを示します。
    """
    
    def __init__(self, detail: str = "バリデーションに失敗しました", error_details: Optional[Dict[str, Any]] = None):
        """
        バリデーションエラーの初期化
        
        引数:
            detail: エラーメッセージ
            error_details: バリデーションエラーの詳細情報
            
        戻り値:
            ValidationError: バリデーションエラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            error_details=error_details
        )
        BusinessLogger.warning(f"バリデーションエラー: {detail}")


class ResourceNotFoundError(CustomHTTPException):
    """
    リソース未発見エラークラス
    
    指定されたリソースが存在しない場合のエラーを処理します。
    404 Not Foundステータスコードを返します。
    """
    
    def __init__(self, resource: str = "Resource"):
        """
        リソース未発見エラーの初期化
        
        引数:
            resource: 見つからないリソース名
            
        戻り値:
            ResourceNotFoundError: リソース未発見エラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} が見つかりません",
            error_code="RESOURCE_NOT_FOUND"
        )
        BusinessLogger.info(f"リソース未発見: {resource}")


class ConflictError(CustomHTTPException):
    """
    競合エラークラス
    
    リソースの競合に関するエラーを処理します。
    409 Conflictステータスコードを返します。
    """
    
    def __init__(self, detail: str = "リソースの競合が発生しました"):
        """
        競合エラーの初期化
        
        引数:
            detail: エラーメッセージ
            
        戻り値:
            ConflictError: 競合エラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT_ERROR"
        )
        BusinessLogger.warning(f"リソース競合: {detail}")


class RateLimitError(CustomHTTPException):
    """
    レート制限エラークラス
    
    レート制限を超過した場合のエラーを処理します。
    429 Too Many Requestsステータスコードを返します。
    """
    
    def __init__(self, detail: str = "レート制限を超過しました"):
        """
        レート制限エラーの初期化
        
        引数:
            detail: エラーメッセージ
            
        戻り値:
            RateLimitError: レート制限エラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED"
        )
        SecurityLogger.warning(f"レート制限超過: {detail}")


class BusinessLogicError(CustomHTTPException):
    """
    ビジネスロジックエラークラス
    
    ビジネスルールに違反した場合のエラーを処理します。
    422 Unprocessable Entityステータスコードを返します。
    """
    
    def __init__(self, detail: str = "ビジネスロジックエラーが発生しました"):
        """
        ビジネスロジックエラーの初期化
        
        引数:
            detail: エラーメッセージ
            
        戻り値:
            BusinessLogicError: ビジネスロジックエラーインスタンス
        """
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="BUSINESS_LOGIC_ERROR"
        )
        BusinessLogger.error(f"ビジネスロジックエラー: {detail}")


# 特定のシナリオ用のエラークラス
class UserNotFoundError(ResourceNotFoundError):
    """
    ユーザー未発見エラークラス
    
    ユーザーが存在しない場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        ユーザー未発見エラーの初期化
        
        戻り値:
            UserNotFoundError: ユーザー未発見エラーインスタンス
        """
        super().__init__("ユーザー")


class TenantNotFoundError(ResourceNotFoundError):
    """
    テナント未発見エラークラス
    
    テナントが存在しない場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        テナント未発見エラーの初期化
        
        戻り値:
            TenantNotFoundError: テナント未発見エラーインスタンス
        """
        super().__init__("テナント")


class ApiKeyNotFoundError(ResourceNotFoundError):
    """
    APIキー未発見エラークラス
    
    APIキーが存在しない場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        APIキー未発見エラーの初期化
        
        戻り値:
            ApiKeyNotFoundError: APIキー未発見エラーインスタンス
        """
        super().__init__("APIキー")


class EmailAlreadyExistsError(ConflictError):
    """
    メールアドレス重複エラークラス
    
    メールアドレスが既に登録されている場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        メールアドレス重複エラーの初期化
        
        戻り値:
            EmailAlreadyExistsError: メールアドレス重複エラーインスタンス
        """
        super().__init__("メールアドレスは既に登録されています")


class UsernameAlreadyExistsError(ConflictError):
    """
    ユーザー名重複エラークラス
    
    ユーザー名が既に使用されている場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        ユーザー名重複エラーの初期化
        
        戻り値:
            UsernameAlreadyExistsError: ユーザー名重複エラーインスタンス
        """
        super().__init__("ユーザー名は既に使用されています")


class InvalidCredentialsError(AuthenticationError):
    """
    無効な認証情報エラークラス
    
    メールアドレスまたはパスワードが間違っている場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        無効な認証情報エラーの初期化
        
        戻り値:
            InvalidCredentialsError: 無効な認証情報エラーインスタンス
        """
        super().__init__("メールアドレスまたはパスワードが正しくありません")


class InactiveUserError(AuthenticationError):
    """
    非アクティブユーザーエラークラス
    
    ユーザーアカウントが無効化されている場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        非アクティブユーザーエラーの初期化
        
        戻り値:
            InactiveUserError: 非アクティブユーザーエラーインスタンス
        """
        super().__init__("ユーザーアカウントが無効化されています")


class TokenExpiredError(AuthenticationError):
    """
    トークン期限切れエラークラス
    
    JWTトークンの有効期限が切れている場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        トークン期限切れエラーの初期化
        
        戻り値:
            TokenExpiredError: トークン期限切れエラーインスタンス
        """
        super().__init__("トークンの有効期限が切れています")


class InvalidTokenError(AuthenticationError):
    """
    無効なトークンエラークラス
    
    JWTトークンが無効な場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        無効なトークンエラーの初期化
        
        戻り値:
            InvalidTokenError: 無効なトークンエラーインスタンス
        """
        super().__init__("無効なトークンです")


class InsufficientPermissionsError(AuthorizationError):
    """
    権限不足エラークラス
    
    ユーザーに必要な権限がない場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        権限不足エラーの初期化
        
        戻り値:
            InsufficientPermissionsError: 権限不足エラーインスタンス
        """
        super().__init__("権限が不足しています")


class TenantAccessDeniedError(AuthorizationError):
    """
    テナントアクセス拒否エラークラス
    
    テナントリソースへのアクセスが拒否された場合のエラーを処理します。
    """
    
    def __init__(self):
        """
        テナントアクセス拒否エラーの初期化
        
        戻り値:
            TenantAccessDeniedError: テナントアクセス拒否エラーインスタンス
        """
        super().__init__("テナントリソースへのアクセスが拒否されました")


class PasswordValidationError(ValidationError):
    """
    パスワードバリデーションエラークラス
    
    パスワードの検証に失敗した場合のエラーを処理します。
    """
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        """
        パスワードバリデーションエラーの初期化
        
        引数:
            details: バリデーションエラーの詳細情報
            
        戻り値:
            PasswordValidationError: パスワードバリデーションエラーインスタンス
        """
        super().__init__("パスワードのバリデーションに失敗しました", details)


class EmailValidationError(ValidationError):
    """
    メールアドレスバリデーションエラークラス
    
    メールアドレスの検証に失敗した場合のエラーを処理します。
    """
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        """
        メールアドレスバリデーションエラーの初期化
        
        引数:
            details: バリデーションエラーの詳細情報
            
        戻り値:
            EmailValidationError: メールアドレスバリデーションエラーインスタンス
        """
        super().__init__("メールアドレスのバリデーションに失敗しました", details)
