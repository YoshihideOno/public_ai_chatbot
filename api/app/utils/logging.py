import logging
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from contextlib import contextmanager
import traceback
from functools import wraps
import asyncio
from app.core.config import settings


class StructuredLogger:
    """構造化ログ出力クラス"""
    
    def __init__(self, name: str = "rag_chatbot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """ログエントリ作成"""
        entry = {
            "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
            "level": level,
            "message": message,
            "service": "rag-chatbot-api",
            "environment": settings.ENVIRONMENT,
        }
        
        # 追加フィールドをマージ
        entry.update(kwargs)
        
        return entry
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        entry = self._create_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(entry, ensure_ascii=False))
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        entry = self._create_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(entry, ensure_ascii=False))
    
    def error(self, message: str, **kwargs):
        """エラーログ"""
        entry = self._create_log_entry("ERROR", message, **kwargs)
        self.logger.error(json.dumps(entry, ensure_ascii=False))
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        if settings.DEBUG:
            entry = self._create_log_entry("DEBUG", message, **kwargs)
            self.logger.debug(json.dumps(entry, ensure_ascii=False))
    
    def critical(self, message: str, **kwargs):
        """クリティカルログ"""
        entry = self._create_log_entry("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(entry, ensure_ascii=False))


# グローバルロガーインスタンス
logger = StructuredLogger()


class RequestLogger:
    """リクエストログクラス"""
    
    @staticmethod
    def log_request(
        method: str,
        path: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        """リクエストログ出力"""
        logger.info(
            "API Request",
            event="request",
            method=method,
            path=path,
            user_id=user_id,
            tenant_id=tenant_id,
            request_id=request_id,
            **kwargs
        )
    
    @staticmethod
    def log_response(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        """レスポンスログ出力"""
        level = "INFO" if status_code < 400 else "WARNING" if status_code < 500 else "ERROR"
        
        log_method = getattr(logger, level.lower())
        log_method(
            "API Response",
            event="response",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            tenant_id=tenant_id,
            request_id=request_id,
            **kwargs
        )


class SecurityLogger:
    """セキュリティログクラス"""
    
    @staticmethod
    def log_auth_attempt(
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        """認証試行ログ"""
        level = "INFO" if success else "WARNING"
        log_method = getattr(logger, level.lower())
        
        log_method(
            "Authentication Attempt",
            event="auth_attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    
    @staticmethod
    def log_permission_denied(
        user_id: str,
        resource: str,
        action: str,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """権限拒否ログ"""
        logger.warning(
            "Permission Denied",
            event="permission_denied",
            user_id=user_id,
            resource=resource,
            action=action,
            tenant_id=tenant_id,
            **kwargs
        )
    
    @staticmethod
    def log_suspicious_activity(
        user_id: Optional[str],
        activity: str,
        details: Dict[str, Any],
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """不審な活動ログ"""
        logger.warning(
            "Suspicious Activity",
            event="suspicious_activity",
            user_id=user_id,
            activity=activity,
            details=details,
            tenant_id=tenant_id,
            **kwargs
        )


class BusinessLogger:
    """ビジネスログクラス"""
    
    @staticmethod
    def log_user_action(
        user_id: str,
        action: str,
        resource: str,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """ユーザーアクションログ"""
        logger.info(
            "User Action",
            event="user_action",
            user_id=user_id,
            action=action,
            resource=resource,
            tenant_id=tenant_id,
            **kwargs
        )
    
    @staticmethod
    def log_tenant_action(
        tenant_id: str,
        action: str,
        details: Dict[str, Any],
        **kwargs
    ):
        """テナントアクションログ"""
        logger.info(
            "Tenant Action",
            event="tenant_action",
            tenant_id=tenant_id,
            action=action,
            details=details,
            **kwargs
        )
    
    @staticmethod
    def log_content_action(
        content_id: str,
        action: str,
        user_id: str,
        tenant_id: str,
        **kwargs
    ):
        """コンテンツアクションログ"""
        logger.info(
            "Content Action",
            event="content_action",
            content_id=content_id,
            action=action,
            user_id=user_id,
            tenant_id=tenant_id,
            **kwargs
        )


class PerformanceLogger:
    """パフォーマンスログクラス"""
    
    @staticmethod
    def log_slow_query(
        query: str,
        duration_ms: float,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """スロークエリログ"""
        logger.warning(
            "Slow Query",
            event="slow_query",
            query=query[:200],  # クエリを200文字に制限
            duration_ms=duration_ms,
            tenant_id=tenant_id,
            **kwargs
        )
    
    @staticmethod
    def log_api_performance(
        endpoint: str,
        duration_ms: float,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """APIパフォーマンスログ"""
        logger.info(
            "API Performance",
            event="api_performance",
            endpoint=endpoint,
            duration_ms=duration_ms,
            tenant_id=tenant_id,
            **kwargs
        )
    
    @staticmethod
    def log_llm_performance(
        model: str,
        tokens_in: int,
        tokens_out: int,
        duration_ms: float,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """LLMパフォーマンスログ"""
        logger.info(
            "LLM Performance",
            event="llm_performance",
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            tenant_id=tenant_id,
            **kwargs
        )


class ErrorLogger:
    """エラーログクラス"""
    
    @staticmethod
    def log_exception(
        exception: Exception,
        context: Dict[str, Any],
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """例外ログ"""
        logger.error(
            "Exception Occurred",
            event="exception",
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback=traceback.format_exc(),
            context=context,
            tenant_id=tenant_id,
            **kwargs
        )
    
    @staticmethod
    def log_validation_error(
        field: str,
        value: Any,
        error_message: str,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """バリデーションエラーログ"""
        logger.warning(
            "Validation Error",
            event="validation_error",
            field=field,
            value=str(value)[:100],  # 値を100文字に制限
            error_message=error_message,
            tenant_id=tenant_id,
            **kwargs
        )


class LoggingMiddleware:
    """ログミドルウェア"""
    
    @staticmethod
    def log_function_call(func):
        """関数呼び出しログデコレータ"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            function_name = f"{func.__module__}.{func.__name__}"
            
            try:
                logger.debug(f"Function call started: {function_name}")
                result = await func(*args, **kwargs)
                
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.debug(
                    f"Function call completed: {function_name}",
                    duration_ms=duration
                )
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                ErrorLogger.log_exception(
                    e,
                    {"function": function_name, "duration_ms": duration}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            function_name = f"{func.__module__}.{func.__name__}"
            
            try:
                logger.debug(f"Function call started: {function_name}")
                result = func(*args, **kwargs)
                
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.debug(
                    f"Function call completed: {function_name}",
                    duration_ms=duration
                )
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                ErrorLogger.log_exception(
                    e,
                    {"function": function_name, "duration_ms": duration}
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class MonitoringUtils:
    """監視ユーティリティ"""
    
    @staticmethod
    @contextmanager
    def measure_time(operation_name: str, tenant_id: Optional[str] = None):
        """実行時間測定コンテキストマネージャー"""
        start_time = datetime.utcnow()
        try:
            yield
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            PerformanceLogger.log_api_performance(
                operation_name,
                duration,
                tenant_id=tenant_id
            )
    
    @staticmethod
    def log_health_check(service: str, status: str, details: Dict[str, Any]):
        """ヘルスチェックログ"""
        logger.info(
            "Health Check",
            event="health_check",
            service=service,
            status=status,
            details=details
        )
    
    @staticmethod
    def log_resource_usage(
        resource_type: str,
        usage: float,
        limit: float,
        tenant_id: Optional[str] = None
    ):
        """リソース使用量ログ"""
        usage_percentage = (usage / limit) * 100 if limit > 0 else 0
        
        level = "WARNING" if usage_percentage > 80 else "INFO"
        log_method = getattr(logger, level.lower())
        
        log_method(
            "Resource Usage",
            event="resource_usage",
            resource_type=resource_type,
            usage=usage,
            limit=limit,
            usage_percentage=usage_percentage,
            tenant_id=tenant_id
        )


# ログ設定の初期化
def setup_logging():
    """ログ設定の初期化"""
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # 外部ライブラリのログレベル調整
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger.info("Logging system initialized")
